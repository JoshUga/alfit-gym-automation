"""Workout Service business logic."""

import os
import json
import httpx
from sqlalchemy.orm import Session
from shared.exceptions import ValidationException
from services.workout_service.models import WorkoutPlan
from services.workout_service.schemas import (
    WorkoutPlanGenerateRequest,
    WorkoutPlanResponse,
    WorkoutPlanUpdateRequest,
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000").rstrip("/")


def _training_days_text(training_days: list[str] | None) -> str:
    if not training_days:
        return "Not specified"
    return ", ".join(day.strip() for day in training_days if day.strip()) or "Not specified"


def _fallback_plan(member_name: str, target: str | None, training_days: list[str] | None) -> str:
    days_text = _training_days_text(training_days)
    target_text = target or "general fitness"
    primary_day = (training_days or ["Monday"])[0]
    secondary_day = (training_days or ["Wednesday"])[1] if len(training_days or []) > 1 else "Wednesday"
    tertiary_day = (training_days or ["Friday"])[2] if len(training_days or []) > 2 else "Friday"
    return (
        "<workout_plan>\n"
        f"  <member_name>{member_name}</member_name>\n"
        f"  <goal>{target_text}</goal>\n"
        "  <training_days>\n"
        + "\n".join(f"    <day>{day}</day>" for day in (training_days or ["Monday", "Wednesday", "Friday"]))
        + "\n"
        "  </training_days>\n"
        "  <weekly_plan>\n"
        "    <week number=\"1\">\n"
        "      <focus>Foundation and technique</focus>\n"
        "      <session>\n"
        f"        <day>{primary_day}</day>\n"
        "        <warmup>8 minutes bike + dynamic mobility</warmup>\n"
        "        <main>Squat 4x6, Bench Press 4x6, Row 4x8</main>\n"
        "        <conditioning>10 minute easy intervals</conditioning>\n"
        "      </session>\n"
        "    </week>\n"
        "    <week number=\"2\">\n"
        "      <focus>Volume progression</focus>\n"
        "      <session>\n"
        f"        <day>{secondary_day}</day>\n"
        "        <warmup>5 minutes row + activation drills</warmup>\n"
        "        <main>Deadlift 4x5, Overhead Press 4x6, Pull-ups 4x8</main>\n"
        "        <conditioning>12 minute tempo cardio</conditioning>\n"
        "      </session>\n"
        "    </week>\n"
        "    <week number=\"3\">\n"
        "      <focus>Intensity progression</focus>\n"
        "      <session>\n"
        f"        <day>{tertiary_day}</day>\n"
        "        <warmup>Mobility flow + core prep</warmup>\n"
        "        <main>Front Squat 5x4, Incline Press 5x5, RDL 4x8</main>\n"
        "        <conditioning>6 rounds moderate circuits</conditioning>\n"
        "      </session>\n"
        "    </week>\n"
        "    <week number=\"4\">\n"
        "      <focus>Deload and form quality</focus>\n"
        "      <session>\n"
        f"        <day>{primary_day}</day>\n"
        "        <warmup>Light cardio + full-body mobility</warmup>\n"
        "        <main>Reduce load by 20%, keep movement quality high</main>\n"
        "        <conditioning>Recovery walk and breathing work</conditioning>\n"
        "      </session>\n"
        "    </week>\n"
        "  </weekly_plan>\n"
        f"  <progression>Increase weight or reps each week while preserving form. Planned days: {days_text}.</progression>\n"
        "</workout_plan>"
    )


def _generate_ai_plan(member_id: int, data: WorkoutPlanGenerateRequest) -> tuple[str, str, str]:
    prompt = (
        "Create a practical weekly gym workout plan in strict XML.\n"
        "Rules:\n"
        "- Return XML only. No markdown, no explanations.\n"
        "- Root tag must be <workout_plan>.\n"
        "- Include tags: <member_name>, <goal>, <training_days>, <weekly_plan>, <progression>.\n"
        "- <training_days> must contain one or more <day> tags.\n"
        "- <weekly_plan> must contain at least 4 <week number=\"N\"> nodes.\n"
        "- Each <week> must include <focus> and one or more <session> nodes.\n"
        "- Each <session> must include <day>, <warmup>, <main>, and <conditioning>.\n"
        "- Keep each field concise and actionable.\n"
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
        updated_at=plan.updated_at,
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


def update_workout_plan(db: Session, plan_id: int, data: WorkoutPlanUpdateRequest) -> WorkoutPlanResponse:
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise ValidationException("Workout plan not found")

    plan.plan_text = data.plan_text.strip()
    if data.member_name is not None:
        plan.member_name = data.member_name
    if data.target is not None:
        plan.target = data.target
    if data.training_days is not None:
        plan.training_days = json.dumps(data.training_days)

    db.commit()
    db.refresh(plan)
    return _to_response(plan)
