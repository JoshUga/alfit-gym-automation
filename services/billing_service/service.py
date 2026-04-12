"""Billing Service business logic."""

import os
import re
import uuid
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException
from services.billing_service.models import (
    SubscriptionPlan,
    Subscription,
    Payment,
    SubscriptionStatus,
    DomainOrder,
)
from services.billing_service.schemas import (
    PlanCreate,
    PlanResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    PaymentResponse,
    DomainCheckoutCreate,
    DomainCheckoutResponse,
    DomainPaymentStatusResponse,
)


PAYGATE_API_BASE = os.getenv("PAYGATE_API_BASE", "https://api.paygate.to/control").rstrip("/")
PAYGATE_WALLET_ENDPOINT = os.getenv("PAYGATE_WALLET_ENDPOINT", f"{PAYGATE_API_BASE}/wallet.php")
PAYGATE_PROCESS_PAYMENT_ENDPOINT = os.getenv(
    "PAYGATE_PROCESS_PAYMENT_ENDPOINT",
    f"{PAYGATE_API_BASE}/payment.php",
)
PAYGATE_STATUS_ENDPOINT = os.getenv("PAYGATE_STATUS_ENDPOINT", f"{PAYGATE_API_BASE}/payment-status.php")
PAYGATE_CONVERT_ENDPOINT = os.getenv("PAYGATE_CONVERT_ENDPOINT", f"{PAYGATE_API_BASE}/convert.php")
PAYGATE_MERCHANT_WALLET = os.getenv("PAYGATE_MERCHANT_WALLET", "").strip()
PAYGATE_CALLBACK_BASE_URL = os.getenv("PAYGATE_CALLBACK_BASE_URL", "").strip()
PAYGATE_PROVIDER = os.getenv("PAYGATE_PROVIDER", "").strip()
PAYGATE_CURRENCY = os.getenv("PAYGATE_CURRENCY", "USD")
DOMAIN_YEAR_PRICE = float(os.getenv("DOMAIN_YEAR_PRICE", "12"))


def _normalize_domain(raw_domain: str) -> str:
    normalized = (raw_domain or "").strip().lower()
    normalized = re.sub(r"^https?://", "", normalized)
    normalized = normalized.split("/", 1)[0]
    return normalized


def create_domain_checkout(db: Session, data: DomainCheckoutCreate) -> DomainCheckoutResponse:
    domain_name = _normalize_domain(data.domain_name)
    years = max(1, int(data.years or 1))
    amount = round(DOMAIN_YEAR_PRICE * years, 2)
    reference = f"dom_{data.gym_id}_{uuid.uuid4().hex[:12]}"

    if not PAYGATE_MERCHANT_WALLET:
        raise ValueError("PAYGATE_MERCHANT_WALLET is required")
    if not PAYGATE_CALLBACK_BASE_URL:
        raise ValueError("PAYGATE_CALLBACK_BASE_URL is required")

    callback_url = (
        f"{PAYGATE_CALLBACK_BASE_URL}"
        f"?reference={reference}&gym_id={data.gym_id}&domain={domain_name}"
    )

    with httpx.Client(timeout=20.0) as client:
        wallet_res = client.get(
            PAYGATE_WALLET_ENDPOINT,
            params={
                "address": PAYGATE_MERCHANT_WALLET,
                "callback": callback_url,
            },
        )
    if wallet_res.status_code >= 400:
        raise ValueError(f"paygate_wallet_failed_{wallet_res.status_code}")

    wallet_payload = wallet_res.json() if wallet_res.content else {}
    address_in = str(wallet_payload.get("address_in") or "")
    polygon_address_in = str(wallet_payload.get("polygon_address_in") or "")
    ipn_token = str(wallet_payload.get("ipn_token") or "")
    if not address_in:
        raise ValueError("paygate_wallet_missing_address_in")

    value = amount
    from_currency = PAYGATE_CURRENCY.upper().strip() or "USD"
    if from_currency != "USD":
        with httpx.Client(timeout=20.0) as client:
            convert_res = client.get(
                PAYGATE_CONVERT_ENDPOINT,
                params={"from": from_currency, "value": value},
            )
        if convert_res.status_code < 400:
            convert_payload = convert_res.json() if convert_res.content else {}
            converted = str(convert_payload.get("value_coin") or "").strip()
            if converted:
                try:
                    value = float(converted)
                    from_currency = "USD"
                except ValueError:
                    pass

    pay_params = {
        "address": address_in,
        "from": from_currency,
        "value": value,
    }
    if PAYGATE_PROVIDER:
        pay_params["provider"] = PAYGATE_PROVIDER

    checkout_url = f"{PAYGATE_PROCESS_PAYMENT_ENDPOINT}?{urlencode(pay_params)}"

    order = DomainOrder(
        gym_id=data.gym_id,
        domain_name=domain_name,
        years=years,
        amount=amount,
        currency=PAYGATE_CURRENCY,
        provider="paygate",
        payment_reference=reference,
        checkout_url=checkout_url,
        callback_url=callback_url,
        address_in=address_in,
        polygon_address_in=polygon_address_in,
        ipn_token=ipn_token or None,
        status="pending",
    )
    db.add(order)
    db.commit()

    return DomainCheckoutResponse(
        domain_name=domain_name,
        years=years,
        amount=amount,
        currency=PAYGATE_CURRENCY,
        checkout_url=checkout_url,
        reference=reference,
        ipn_token=ipn_token or None,
    )


def handle_paygate_callback(db: Session, payload: dict) -> DomainPaymentStatusResponse:
    reference = str(payload.get("reference") or "").strip()
    if not reference:
        raise NotFoundException("DomainOrder", "missing_reference")

    order = db.query(DomainOrder).filter(DomainOrder.payment_reference == reference).first()
    if not order:
        raise NotFoundException("DomainOrder", reference)

    value_coin = str(payload.get("value_coin") or "").strip()
    coin = str(payload.get("coin") or "").strip()
    txid_in = str(payload.get("txid_in") or "").strip()
    txid_out = str(payload.get("txid_out") or "").strip()
    value_forwarded_coin = str(payload.get("value_forwarded_coin") or "").strip()

    if value_coin:
        order.status = "paid"
    else:
        order.status = order.status or "pending"

    order.paid_value_coin = value_coin or order.paid_value_coin
    order.paid_coin = coin or order.paid_coin
    order.txid_in = txid_in or order.txid_in
    order.txid_out = txid_out or order.txid_out
    order.value_forwarded_coin = value_forwarded_coin or order.value_forwarded_coin
    db.commit()

    return DomainPaymentStatusResponse(
        reference=order.payment_reference,
        status=order.status,
        domain_name=order.domain_name,
        checkout_url=order.checkout_url,
        txid_out=order.txid_out,
        value_coin=order.paid_value_coin,
        coin=order.paid_coin,
    )


def get_domain_payment_status(db: Session, reference: str) -> DomainPaymentStatusResponse:
    order = db.query(DomainOrder).filter(DomainOrder.payment_reference == reference).first()
    if not order:
        raise NotFoundException("DomainOrder", reference)

    if order.ipn_token:
        try:
            with httpx.Client(timeout=15.0) as client:
                status_res = client.get(PAYGATE_STATUS_ENDPOINT, params={"ipn_token": order.ipn_token})
            if status_res.status_code < 400:
                status_payload = status_res.json() if status_res.content else {}
                remote_status = str(status_payload.get("status") or "").lower()
                if remote_status in {"paid", "unpaid"}:
                    order.status = remote_status
                order.paid_value_coin = str(status_payload.get("value_coin") or order.paid_value_coin or "") or None
                order.paid_coin = str(status_payload.get("coin") or order.paid_coin or "") or None
                order.txid_out = str(status_payload.get("txid_out") or order.txid_out or "") or None
                db.commit()
        except Exception:
            pass

    return DomainPaymentStatusResponse(
        reference=order.payment_reference,
        status=order.status,
        domain_name=order.domain_name,
        checkout_url=order.checkout_url,
        txid_out=order.txid_out,
        value_coin=order.paid_value_coin,
        coin=order.paid_coin,
    )


def create_plan(db: Session, data: PlanCreate) -> PlanResponse:
    """Create a subscription plan."""
    plan = SubscriptionPlan(
        name=data.name,
        price=data.price,
        features=data.features,
        max_phone_numbers=data.max_phone_numbers,
        max_ai_messages=data.max_ai_messages,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return PlanResponse.model_validate(plan)


def list_plans(db: Session) -> list[PlanResponse]:
    """List all active subscription plans."""
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active.is_(True)).all()
    return [PlanResponse.model_validate(p) for p in plans]


def create_subscription(db: Session, data: SubscriptionCreate) -> SubscriptionResponse:
    """Subscribe a gym to a plan."""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == data.plan_id).first()
    if not plan:
        raise NotFoundException("SubscriptionPlan", data.plan_id)

    subscription = Subscription(
        gym_id=data.gym_id,
        plan_id=data.plan_id,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return SubscriptionResponse.model_validate(subscription)


def get_subscription(db: Session, sub_id: int) -> SubscriptionResponse:
    """Get a subscription by ID."""
    subscription = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not subscription:
        raise NotFoundException("Subscription", sub_id)
    return SubscriptionResponse.model_validate(subscription)


def cancel_subscription(db: Session, sub_id: int) -> SubscriptionResponse:
    """Cancel a subscription."""
    subscription = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not subscription:
        raise NotFoundException("Subscription", sub_id)
    subscription.status = SubscriptionStatus.CANCELLED
    db.commit()
    db.refresh(subscription)
    return SubscriptionResponse.model_validate(subscription)


def get_payment_history(db: Session, gym_id: int) -> list[PaymentResponse]:
    """Get payment history for a gym."""
    payments = db.query(Payment).filter(Payment.gym_id == gym_id).order_by(Payment.created_at.desc()).all()
    return [PaymentResponse.model_validate(p) for p in payments]
