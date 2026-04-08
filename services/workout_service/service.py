"""Workout Service business logic."""

import os
import json
import httpx
from sqlalchemy.orm import Session
from shared.exceptions import ValidationException
from services.workout_service.models import WorkoutPlan
from services.workout_service.schemas import WorkoutPlanGenerateRequest, WorkoutPlanResponse

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000").rstrip("/")


def _training_days_text(training_days: list[str] | None) -> str:
    if not training_days:
        return "Not specified"
    return ", ".join(day.strip() for day in training_days if day.strip()) or "Not specified"


def _fallback_plan(member_name: str, target: str | None, training_days: list[str] | None) -> str:
    days_text = _training_days_text(training_days)
    target_text = target or "general fitness"
    return (
        f"Workout Plan for {member_name}\n"
        f"Goal: {target_text}\n"
        f"Training Days: {days_text}\n\n"
        "Session A: Compound strength (squats, bench press, rows) + core\n"
        "Session B: Hypertrophy focus (push, pull, legs split)\n"
        "Session C: Conditioning + mobility + recovery work\n\n"
        "Progression: Increase weight or reps weekly while maintaining clean form."
    )


def _generate_ai_plan(member_id: int, data: WorkoutPlanGenerateRequest) -> tuple[str, str, str]:
    prompt = (
        "Create a practical weekly gym workout plan.\n"
        "Rules:\n"
        "- Keep it concise and actionable.\n"
        "- Include warm-up, main exercises, sets/reps, and recovery notes.\n"
        "- Mention progression guidance for 4 weeks.\n"
        "- Plain text only, no markdown table.\n"
        f"Member name: {data.member_name}\n"
        f"Member id: {member_id}\n"
        f"Goal: {data.target or 'general fitness'}\n"
        f"Training days: {_training_days_text(data.training_days)}"
    )

    payload = {
        "gym_id": data.gym_id,
        "phone_number_id": 0,
        "incoming_message": prompt,
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                f"{AI_SERVICE_URL}/api/v1/ai/generate-response/internal",
                json=payload,
            )
        if response.status_code >= 400:
            raise ValidationException(f"AI generation failed with status {response.status_code}")

        body = response.json() if response.content else {}
        result = body.get("data") if isinstance(body, dict) else None
        if not isinstance(result, dict):
            raise ValidationException("Invalid AI response payload")

        text = str(result.get("response_text") or "").strip()
        if not text:
            raise ValidationException("AI returned an empty workout plan")

        return text, str(result.get("provider") or "ai"), str(result.get("model") or "runtime")
    except Exception:
        return _fallback_plan(data.member_name, data.target, data.training_days), "fallback", "template"


def _to_response(plan: WorkoutPlan) -> WorkoutPlanResponse:
    parsed_days = None
    if plan.training_days:
        try:
            payload = json.loads(plan.training_days)
            if isinstance(payload, list):
                parsed_days = [str(day) for day in payload]
        except Exception:
            parsed_days = None
    return WorkoutPlanResponse(
        id=plan.id,
        gym_id=plan.gym_id,
        member_id=plan.member_id,
        member_name=plan.member_name,
        target=plan.target,
        training_days=parsed_days,
        plan_text=plan.plan_text,
        provider=plan.provider,
        model=plan.model,
        generated_by_ai=plan.generated_by_ai,
        created_at=plan.created_at,
    )


def get_latest_workout_plan(db: Session, gym_id: int, member_id: int) -> WorkoutPlanResponse | None:
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.gym_id == gym_id, WorkoutPlan.member_id == member_id)
        .order_by(WorkoutPlan.id.desc())
        .first()
    )
    if not plan:
        return None
    return _to_response(plan)


def generate_workout_plan(db: Session, member_id: int, data: WorkoutPlanGenerateRequest) -> WorkoutPlanResponse:
    plan_text, provider, model = _generate_ai_plan(member_id, data)

    plan = WorkoutPlan(
        gym_id=data.gym_id,
        member_id=member_id,
        member_name=data.member_name,
        target=data.target,
        training_days=json.dumps(data.training_days or []),
        plan_text=plan_text,
        provider=provider,
        model=model,
        generated_by_ai=(provider != "fallback"),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _to_response(plan)
