"""Workout Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.workout_service.schemas import (
    WorkoutPlanGenerateRequest,
    WorkoutPlanUpdateRequest,
    WorkoutPlanResponse,
)
from services.workout_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.get("/gyms/{gym_id}/members/{member_id}/workout-plan", response_model=APIResponse[WorkoutPlanResponse | None])
def get_member_workout_plan(
    gym_id: int,
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get latest workout plan for a member."""
    result = service.get_latest_workout_plan(db, gym_id, member_id)
    return APIResponse(data=result)


@router.post("/members/{member_id}/workout-plan/generate", response_model=APIResponse[WorkoutPlanResponse])
def generate_member_workout_plan(
    member_id: int,
    data: WorkoutPlanGenerateRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Generate and save a member workout plan using AI service."""
    result = service.generate_workout_plan(db, member_id, data)
    return APIResponse(data=result, message="Workout plan generated")


@router.put("/workout-plans/{plan_id}", response_model=APIResponse[WorkoutPlanResponse])
def update_workout_plan(
    plan_id: int,
    data: WorkoutPlanUpdateRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update a workout plan (used to edit XML structured plans)."""
    result = service.update_workout_plan(db, plan_id, data)
    return APIResponse(data=result, message="Workout plan updated")
