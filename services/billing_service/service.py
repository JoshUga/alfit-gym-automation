"""Billing Service business logic."""

from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException
from services.billing_service.models import (
    SubscriptionPlan,
    Subscription,
    Payment,
    SubscriptionStatus,
)
from services.billing_service.schemas import (
    PlanCreate,
    PlanResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    PaymentResponse,
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
