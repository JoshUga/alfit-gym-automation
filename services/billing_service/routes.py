"""Billing Service API routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, require_roles, UserClaims
from shared.models import APIResponse
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
from services.billing_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/plans", response_model=APIResponse[PlanResponse])
def create_plan(
    data: PlanCreate,
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """Create a subscription plan (admin only)."""
    result = service.create_plan(db, data)
    return APIResponse(data=result, message="Plan created successfully")


@router.get("/plans", response_model=APIResponse[list[PlanResponse]])
def list_plans(db: Session = Depends(get_session)):
    """List all active subscription plans."""
    result = service.list_plans(db)
    return APIResponse(data=result)


@router.post("/subscriptions", response_model=APIResponse[SubscriptionResponse])
def create_subscription(
    data: SubscriptionCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Subscribe a gym to a plan."""
    result = service.create_subscription(db, data)
    return APIResponse(data=result, message="Subscription created successfully")


@router.get("/subscriptions/{sub_id}", response_model=APIResponse[SubscriptionResponse])
def get_subscription(
    sub_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get subscription details."""
    result = service.get_subscription(db, sub_id)
    return APIResponse(data=result)


@router.put("/subscriptions/{sub_id}/cancel", response_model=APIResponse[SubscriptionResponse])
def cancel_subscription(
    sub_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Cancel a subscription."""
    result = service.cancel_subscription(db, sub_id)
    return APIResponse(data=result, message="Subscription cancelled")


@router.get("/gyms/{gym_id}/payments", response_model=APIResponse[list[PaymentResponse]])
def get_payment_history(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get payment history for a gym."""
    result = service.get_payment_history(db, gym_id)
    return APIResponse(data=result)


@router.post("/domains/checkout", response_model=APIResponse[DomainCheckoutResponse])
def create_domain_checkout(
    data: DomainCheckoutCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create checkout link for domain purchase via PayGate."""
    result = service.create_domain_checkout(db, data)
    return APIResponse(data=result, message="Domain checkout created")


@router.get("/domains/{reference}/status", response_model=APIResponse[DomainPaymentStatusResponse])
def get_domain_checkout_status(
    reference: str,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get domain checkout payment status."""
    result = service.get_domain_payment_status(db, reference)
    return APIResponse(data=result)


@router.get("/domains/paygate/callback", response_model=APIResponse[DomainPaymentStatusResponse])
def paygate_callback(
    request: Request,
    db: Session = Depends(get_session),
):
    """PayGate callback endpoint to mark domain order as paid."""
    payload = dict(request.query_params)
    result = service.handle_paygate_callback(db, payload)
    return APIResponse(data=result, message="Callback processed")
