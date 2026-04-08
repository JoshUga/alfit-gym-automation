"""Gym Service business logic."""

import logging
import os
import httpx
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from shared.exceptions import NotFoundException, ValidationException
from services.gym_service.models import Gym, GymPhoneNumber, EvolutionCredential
from services.gym_service.schemas import (
    GymCreate,
    GymUpdate,
    GymResponse,
    PhoneNumberCreate,
    PhoneNumberResponse,
    EvolutionCredentialCreate,
    EvolutionCredentialResponse,
    WhatsAppConnectRequest,
    WhatsAppConnectResponse,
    WhatsAppStatusResponse,
)


EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://evolution-api:8080").rstrip("/")
EVOLUTION_API_GLOBAL_KEY = os.getenv("EVOLUTION_API_GLOBAL_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "qwen2.5:0.5b").strip()
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "tinyllama").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
EVOLUTION_UPSERT_WEBHOOK_URL = os.getenv(
    "EVOLUTION_UPSERT_WEBHOOK_URL",
    "http://message-service:8000/api/v1/messages/evolution-upsert",
).rstrip("/")
logger = logging.getLogger(__name__)


def register_gym(db: Session, gym_data: GymCreate, owner_id: int) -> GymResponse:
    """Register a new gym."""
    gym = Gym(
        name=gym_data.name,
        address=gym_data.address,
        phone=gym_data.phone,
        email=gym_data.email,
        owner_id=owner_id,
    )
    db.add(gym)
    db.commit()
    db.refresh(gym)
    return GymResponse.model_validate(gym)


def get_owner_gym(db: Session, owner_id: int) -> GymResponse:
    """Get the most recent active gym for the authenticated owner."""
    gym = (
        db.query(Gym)
        .filter(Gym.owner_id == owner_id, Gym.is_active.is_(True))
        .order_by(Gym.id.desc())
        .first()
    )
    if not gym:
        raise NotFoundException("Gym", owner_id)
    return GymResponse.model_validate(gym)


def get_gym(db: Session, gym_id: int) -> GymResponse:
    """Get gym by ID."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)
    return GymResponse.model_validate(gym)


def update_gym(db: Session, gym_id: int, gym_data: GymUpdate) -> GymResponse:
    """Update gym details."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    update_data = gym_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(gym, field, value)

    db.commit()
    db.refresh(gym)
    return GymResponse.model_validate(gym)


def delete_gym(db: Session, gym_id: int) -> dict:
    """Soft-delete a gym."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)
    gym.is_active = False
    db.commit()
    return {"message": "Gym deleted successfully"}


def add_phone_number(db: Session, gym_id: int, data: PhoneNumberCreate) -> PhoneNumberResponse:
    """Add a phone number to a gym."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    phone = GymPhoneNumber(
        gym_id=gym_id,
        phone_number=data.phone_number,
        label=data.label,
    )
    db.add(phone)
    db.commit()
    db.refresh(phone)
    return PhoneNumberResponse.model_validate(phone)


def list_phone_numbers(db: Session, gym_id: int) -> list[PhoneNumberResponse]:
    """List all phone numbers for a gym."""
    phones = db.query(GymPhoneNumber).filter(GymPhoneNumber.gym_id == gym_id).all()
    return [PhoneNumberResponse.model_validate(p) for p in phones]


def remove_phone_number(db: Session, gym_id: int, phone_id: int) -> dict:
    """Remove a phone number from a gym."""
    phone = (
        db.query(GymPhoneNumber)
        .filter(GymPhoneNumber.id == phone_id, GymPhoneNumber.gym_id == gym_id)
        .first()
    )
    if not phone:
        raise NotFoundException("PhoneNumber", phone_id)
    db.delete(phone)
    db.commit()
    return {"message": "Phone number removed successfully"}


def set_evolution_credentials(
    db: Session, gym_id: int, data: EvolutionCredentialCreate
) -> EvolutionCredentialResponse:
    """Set Evolution API credentials for a gym."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    cred = EvolutionCredential(
        gym_id=gym_id,
        api_key=data.api_key,
        instance_name=data.instance_name,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return EvolutionCredentialResponse.model_validate(cred)


def get_evolution_credentials(db: Session, gym_id: int) -> list[EvolutionCredentialResponse]:
    """Get Evolution API credentials for a gym."""
    creds = db.query(EvolutionCredential).filter(EvolutionCredential.gym_id == gym_id).all()
    return [EvolutionCredentialResponse.model_validate(c) for c in creds]


def _latest_credential(db: Session, gym_id: int) -> EvolutionCredential:
    cred = (
        db.query(EvolutionCredential)
        .filter(EvolutionCredential.gym_id == gym_id)
        .order_by(EvolutionCredential.id.desc())
        .first()
    )
    if not cred:
        raise ValidationException(
            "No Evolution API credentials found for this gym. Save credentials first."
        )
    return cred


def _get_or_create_credential(
    db: Session, gym_id: int, instance_name: str | None = None
) -> EvolutionCredential:
    """Get latest credential or create one from server-side Evolution key."""
    cred = (
        db.query(EvolutionCredential)
        .filter(EvolutionCredential.gym_id == gym_id)
        .order_by(EvolutionCredential.id.desc())
        .first()
    )
    if cred:
        return cred

    if not EVOLUTION_API_GLOBAL_KEY:
        raise ValidationException(
            "Server Evolution API key is not configured. Ask admin to set EVOLUTION_API_GLOBAL_KEY."
        )

    cred = EvolutionCredential(
        gym_id=gym_id,
        api_key=EVOLUTION_API_GLOBAL_KEY,
        instance_name=instance_name or f"gym-{gym_id}",
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred


def _extract_qr_and_pairing(payload: dict) -> tuple[str | None, str | None]:
    qr_code = None
    pairing_code = None

    if isinstance(payload, dict):
        qr_code = (
            payload.get("base64")
            or payload.get("qrcode")
            or payload.get("qr")
            or (payload.get("qrcode") or {}).get("base64")
        )
        pairing_code = (
            payload.get("pairingCode")
            or payload.get("pairing_code")
            or (payload.get("qrcode") or {}).get("pairingCode")
        )

    return qr_code, pairing_code


def _configure_evolution_upsert_webhook(
    client: httpx.Client,
    api_key: str,
    instance_name: str,
) -> dict:
    """Best-effort webhook setup so Evolution forwards upsert events."""
    if not EVOLUTION_UPSERT_WEBHOOK_URL:
        return {"configured": False, "reason": "missing_webhook_url"}

    headers = {"apikey": api_key, "Content-Type": "application/json"}

    payload_variants = [
        {
            "webhook": {
                "enabled": True,
                "url": EVOLUTION_UPSERT_WEBHOOK_URL,
                "webhookByEvents": True,
                "events": ["MESSAGES_UPSERT"],
            }
        },
        {
            "webhook": {
                "enabled": True,
                "url": EVOLUTION_UPSERT_WEBHOOK_URL,
            },
            "events": {
                "MESSAGES_UPSERT": True,
                "CONNECTION_UPDATE": True,
            },
        },
        {
            "enabled": True,
            "url": EVOLUTION_UPSERT_WEBHOOK_URL,
            "events": ["MESSAGES_UPSERT", "messages.upsert"],
            "webhook_by_events": True,
        },
        {
            "enabled": True,
            "webhook": EVOLUTION_UPSERT_WEBHOOK_URL,
            "events": ["MESSAGES_UPSERT", "messages.upsert"],
        },
    ]

    endpoint_variants = [
        f"{EVOLUTION_API_URL}/webhook/set/{instance_name}",
        f"{EVOLUTION_API_URL}/webhook/set/{instance_name}/",
        f"{EVOLUTION_API_URL}/webhook/setWebhook/{instance_name}",
        f"{EVOLUTION_API_URL}/instance/webhook/{instance_name}",
    ]

    for endpoint in endpoint_variants:
        for payload in payload_variants:
            try:
                resp = client.post(endpoint, headers=headers, json=payload)
            except Exception as exc:
                logger.warning(
                    "Evolution webhook setup call failed for %s at %s: %s",
                    instance_name,
                    endpoint,
                    exc,
                )
                continue

            if resp.status_code < 300:
                logger.info(
                    "Configured Evolution upsert webhook for %s via %s",
                    instance_name,
                    endpoint,
                )
                return {"configured": True}

            logger.warning(
                "Evolution webhook setup rejected for %s via %s with HTTP %s: %s",
                instance_name,
                endpoint,
                resp.status_code,
                resp.text,
            )

    return {"configured": False, "reason": "all_webhook_attempts_failed"}


def connect_whatsapp_instance(
    db: Session, gym_id: int, data: WhatsAppConnectRequest
) -> WhatsAppConnectResponse:
    """Create/connect an EvolutionAPI instance and return QR/pairing code data."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    cred = _get_or_create_credential(db, gym_id, data.instance_name)
    instance_name = data.instance_name or cred.instance_name

    if cred.instance_name != instance_name:
        cred.instance_name = instance_name
        db.commit()
        db.refresh(cred)

    api_key = EVOLUTION_API_GLOBAL_KEY or cred.api_key
    if not api_key:
        raise ValidationException("Evolution API key is missing")

    headers = {"apikey": api_key, "Content-Type": "application/json"}
    create_payload = {
        "instanceName": instance_name,
        "token": cred.api_key,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
    }

    with httpx.Client(timeout=30.0) as client:
        create_resp = client.post(
            f"{EVOLUTION_API_URL}/instance/create",
            headers=headers,
            json=create_payload,
        )
        # 409 usually means instance already exists and is safe to continue.
        if create_resp.status_code not in (200, 201, 409):
            raise ValidationException(
                f"Failed to create Evolution instance: {create_resp.text}"
            )

        connect_payload = {}
        if data.phone_number:
            connect_payload["number"] = data.phone_number

        connect_resp = client.get(
            f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
            headers=headers,
            params=connect_payload,
        )
        if connect_resp.status_code >= 400:
            raise ValidationException(
                f"Failed to get connection data: {connect_resp.text}"
            )

        connect_data = connect_resp.json() if connect_resp.content else {}
        qr_code, pairing_code = _extract_qr_and_pairing(connect_data)

        webhook_setup = _configure_evolution_upsert_webhook(client, api_key, instance_name)
        if not webhook_setup.get("configured"):
            logger.warning(
                "WhatsApp connected but Evolution upsert webhook not configured for %s (%s)",
                instance_name,
                webhook_setup.get("reason", "unknown"),
            )

        return WhatsAppConnectResponse(
            instance_name=instance_name,
            status="pending_connection",
            qr_code=qr_code,
            pairing_code=pairing_code,
        )


def get_whatsapp_connection_status(db: Session, gym_id: int) -> WhatsAppStatusResponse:
    """Get current WhatsApp connection status from EvolutionAPI for a gym instance."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    cred = _get_or_create_credential(db, gym_id)
    api_key = EVOLUTION_API_GLOBAL_KEY or cred.api_key
    if not api_key:
        raise ValidationException("Evolution API key is missing")

    with httpx.Client(timeout=20.0) as client:
        resp = client.get(
            f"{EVOLUTION_API_URL}/instance/connectionState/{cred.instance_name}",
            headers={"apikey": api_key},
        )
        if resp.status_code >= 400:
            raise ValidationException(f"Failed to fetch status: {resp.text}")

        data = resp.json() if resp.content else {}
        instance_state = data.get("instance")
        if isinstance(instance_state, dict):
            status = instance_state.get("state") or instance_state.get("status") or "unknown"
        else:
            status = data.get("state") or data.get("status") or instance_state or "unknown"

        return WhatsAppStatusResponse(instance_name=cred.instance_name, status=str(status))


def _compose_welcome_message(gym_name: str, member_name: str, schedule: str | None) -> str:
    lines = [
        f"\U0001f389 Welcome to {gym_name}, {member_name}!",
        "",
        "You have been successfully registered as a member. We are excited to have you!",
    ]
    if schedule:
        lines += ["", "\U0001f4c5 Your Training Schedule:", schedule]
    lines += ["", "Feel free to reach out if you need anything. See you at the gym! \U0001f4aa"]
    return "\n".join(lines)


def send_welcome_to_member(
    db: Session, gym_id: int, member_name: str, member_phone: str, schedule: str | None = None
) -> dict:
    """Send a WhatsApp welcome message to a newly added member."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        return {"status": "skipped", "reason": "gym_not_found"}

    try:
        cred = _latest_credential(db, gym_id)
    except Exception:
        logger.info("No Evolution credentials for gym %s; skipping welcome message", gym_id)
        return {"status": "skipped", "reason": "no_credentials"}

    api_key = EVOLUTION_API_GLOBAL_KEY or cred.api_key
    if not api_key:
        return {"status": "skipped", "reason": "no_api_key"}

    try:
        connection_status = get_whatsapp_connection_status(db, gym_id)
        if not _connected_status(connection_status.status):
            logger.info(
                "Skipping welcome message for gym %s because instance is %s",
                gym_id,
                connection_status.status,
            )
            return {
                "status": "skipped",
                "reason": "instance_not_connected",
            }
    except Exception as exc:
        logger.warning("Could not confirm WhatsApp connection before welcome send: %s", exc)
        return {"status": "skipped", "reason": "status_unavailable"}

    message = _compose_welcome_message(gym.name, member_name, schedule)
    payload = {"number": member_phone, "text": message}
    headers = {"apikey": api_key, "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{EVOLUTION_API_URL}/message/sendText/{cred.instance_name}",
                headers=headers,
                json=payload,
            )
        body: dict | None = None
        try:
            body = resp.json() if resp.content else None
        except Exception:
            body = None

        is_http_ok = resp.status_code < 300
        body_status = str((body or {}).get("status") or "").lower() if isinstance(body, dict) else ""
        is_body_failure = body_status in {"error", "failed", "failure"}

        logger.info(
            "Welcome message to %s via %s → HTTP %s",
            member_phone,
            cred.instance_name,
            resp.status_code,
        )
        if is_http_ok and not is_body_failure:
            return {"status": "sent", "code": resp.status_code}
        return {
            "status": "failed",
            "code": resp.status_code,
            "reason": body_status or "send_rejected",
        }
    except Exception as exc:
        logger.warning("Failed to send welcome WhatsApp to %s: %s", member_phone, exc)
        return {"status": "error", "reason": str(exc)}


def _connected_status(status: str) -> bool:
    return str(status).strip().lower() in {"open", "connected", "online"}


def _generate_ai_onboarding_copy(gym_name: str, owner_name: str | None) -> dict:
    owner_display = (owner_name or "there").strip() or "there"
    provider = AI_PROVIDER
    model = AI_MODEL

    prompt = (
        "Write exactly one short WhatsApp message in English.\n"
        "Goal: welcome a new gym owner after connecting WhatsApp to Alfit.\n"
        "Tone: warm, human, confident, not robotic.\n"
        "Rules:\n"
        "- Include 3 to 5 relevant emojis naturally.\n"
        "- Mention the gym name and Alfit.\n"
        "- Mention that connection is successful.\n"
        "- Give two concrete next actions: add first members and schedule first broadcast.\n"
        "- Keep under 70 words.\n"
        "- No markdown, no bullets, no hashtags.\n"
        "- Output only the final message text, no intro, no labels, no explanation.\n"
        f"Gym name: {gym_name}\n"
        f"Owner name: {owner_display}"
    )

    def _fallback_copy() -> str:
        return (
            f"Hey {owner_display}! 🎉 Your WhatsApp is now connected to Alfit for {gym_name}. "
            "You are all set to start automations 🚀 Add your first members 👥 and schedule your first broadcast 📣 "
            "to kick things off. Need help? We are here for you 💪"
        )

    def _sanitize_generated_copy(text: str) -> str | None:
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        if not cleaned:
            return None

        lower = cleaned.lower()
        banned_fragments = [
            "here is a sample",
            "sample whatsapp",
            "example message",
            "whatsapp message in english",
            "as an ai",
            "i can",
            "i cannot",
        ]
        if any(fragment in lower for fragment in banned_fragments):
            return None
        if cleaned.startswith("-") or cleaned.startswith("*") or "\n-" in cleaned or "\n*" in cleaned:
            return None
        if len(cleaned.split()) > 70:
            return None
        return cleaned

    # Prefer Ollama local generation for deterministic self-hosted behavior.
    if provider == "ollama":
        for candidate_model in [model, AI_FALLBACK_MODEL, "tinyllama"]:
            if not candidate_model:
                continue
            try:
                with httpx.Client(timeout=35.0) as client:
                    resp = client.post(
                        f"{OLLAMA_BASE_URL}/api/generate",
                        json={
                            "model": candidate_model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,
                                "num_predict": 110,
                            },
                        },
                    )
                if resp.status_code >= 400:
                    continue
                payload = resp.json() if resp.content else {}
                text = str(payload.get("response") or "").strip()
                safe_text = _sanitize_generated_copy(text)
                if safe_text:
                    return {"text": safe_text, "provider": provider, "model": candidate_model}
            except Exception:
                continue

    return {
        "text": _fallback_copy(),
        "provider": provider or "fallback",
        "model": model or "template",
    }


def send_onboarding_self_message(
    db: Session, gym_id: int, phone_number: str, owner_name: str | None = None
) -> dict:
    """Send a one-time style onboarding welcome to the owner's own WhatsApp number."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        return {"status": "skipped", "reason": "gym_not_found"}

    if gym.onboarding_welcome_sent_at is not None:
        return {"status": "skipped", "reason": "already_sent"}

    try:
        status_res = get_whatsapp_connection_status(db, gym_id)
    except Exception:
        return {"status": "skipped", "reason": "status_unavailable"}

    if not _connected_status(status_res.status):
        return {"status": "skipped", "reason": "instance_not_connected"}

    try:
        cred = _latest_credential(db, gym_id)
    except Exception:
        return {"status": "skipped", "reason": "no_credentials"}

    api_key = EVOLUTION_API_GLOBAL_KEY or cred.api_key
    if not api_key:
        return {"status": "skipped", "reason": "no_api_key"}

    ai_copy = _generate_ai_onboarding_copy(gym.name, owner_name)
    payload = {"number": phone_number, "text": ai_copy["text"]}

    # Atomic claim to prevent duplicate sends when multiple pollers hit this endpoint.
    claimed = (
        db.query(Gym)
        .filter(
            Gym.id == gym_id,
            Gym.onboarding_welcome_sent_at.is_(None),
        )
        .update({Gym.onboarding_welcome_sent_at: func.now()}, synchronize_session=False)
    )
    db.commit()
    if claimed == 0:
        return {
            "status": "skipped",
            "reason": "already_sent",
            "provider": ai_copy["provider"],
            "model": ai_copy["model"],
        }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{EVOLUTION_API_URL}/message/sendText/{cred.instance_name}",
                headers={"apikey": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        if resp.status_code >= 400:
            db.query(Gym).filter(Gym.id == gym_id).update(
                {Gym.onboarding_welcome_sent_at: None},
                synchronize_session=False,
            )
            db.commit()
            return {
                "status": "failed",
                "reason": f"send_failed_{resp.status_code}",
                "provider": ai_copy["provider"],
                "model": ai_copy["model"],
            }

        return {
            "status": "sent",
            "provider": ai_copy["provider"],
            "model": ai_copy["model"],
        }
    except Exception as exc:
        db.query(Gym).filter(Gym.id == gym_id).update(
            {Gym.onboarding_welcome_sent_at: None},
            synchronize_session=False,
        )
        db.commit()
        return {
            "status": "error",
            "reason": str(exc),
            "provider": ai_copy["provider"],
            "model": ai_copy["model"],
        }
