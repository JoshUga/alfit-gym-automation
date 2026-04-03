"""Gym Service business logic."""

import logging
import os
import httpx
from sqlalchemy.orm import Session
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
EVOLUTION_WEBHOOK_URL = os.getenv(
    "EVOLUTION_WEBHOOK_URL", "http://nginx/evolution/webhooks/incoming"
).rstrip("/")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()
AI_MODEL = os.getenv("AI_MODEL", "SmolLM-135M").strip()
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "smollm:135m").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
logger = logging.getLogger(__name__)


def _normalize_pairing_code(value: str | None) -> str | None:
    """Return a short human-entered pairing code, or None for non-pairing payloads."""
    if not value:
        return None

    code = str(value).strip()
    if not code:
        return None

    # Real pairing codes are short; large/base64 blobs are not user-facing pairing codes.
    if len(code) > 12:
        return None

    if not code.isalnum():
        return None

    return code


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
        pairing_candidate = (
            payload.get("pairingCode")
            or payload.get("pairing_code")
            or payload.get("pairCode")
            or payload.get("pair_code")
            or (payload.get("qrcode") or {}).get("pairingCode")
            or (payload.get("qrcode") or {}).get("pairing_code")
        )
        pairing_code = _normalize_pairing_code(pairing_candidate)

    return qr_code, pairing_code


def _register_incoming_webhook(instance_name: str, api_key: str) -> bool:
    """Register a webhook on the Evolution API instance so incoming messages trigger auto-replies.

    Returns True when the registration succeeds, False otherwise.
    """
    if not EVOLUTION_WEBHOOK_URL:
        logger.warning(
            "EVOLUTION_WEBHOOK_URL is not set; skipping webhook registration for %s",
            instance_name,
        )
        return False

    # Evolution API v2 expects a flat payload without a nested "webhook" key.
    # Event names must use the ALL_CAPS format understood by v2 (MESSAGES_UPSERT).
    payload = {
        "enabled": True,
        "url": EVOLUTION_WEBHOOK_URL,
        "webhookByEvents": False,
        "webhookBase64": False,
        "events": ["MESSAGES_UPSERT"],
    }

    endpoint = f"{EVOLUTION_API_URL}/webhook/set/{instance_name}"

    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(
                endpoint,
                headers={"apikey": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        if resp.status_code < 400:
            logger.info(
                "Webhook registered for instance %s → %s (HTTP %s)",
                instance_name,
                EVOLUTION_WEBHOOK_URL,
                resp.status_code,
            )
            return True
        logger.warning(
            "Webhook registration failed for instance %s: HTTP %s – %s",
            instance_name,
            resp.status_code,
            resp.text[:300],
        )
    except Exception as exc:
        logger.warning(
            "Webhook registration error for instance %s: %s",
            instance_name,
            exc,
        )

    return False


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

        existing_phone = (
            db.query(GymPhoneNumber)
            .filter(
                GymPhoneNumber.gym_id == gym_id,
                GymPhoneNumber.phone_number == data.phone_number,
            )
            .first()
        )
        if not existing_phone:
            db.add(
                GymPhoneNumber(
                    gym_id=gym_id,
                    phone_number=data.phone_number,
                    label="owner_whatsapp",
                    evolution_instance_id=instance_name,
                )
            )
            db.commit()

        webhook_ok = _register_incoming_webhook(instance_name, api_key)
        if not webhook_ok:
            logger.warning(
                "Webhook setup incomplete for gym %s instance %s; "
                "auto-replies will not work until webhook is registered.",
                gym_id,
                instance_name,
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
        logger.info(
            "Welcome message to %s via %s → HTTP %s",
            member_phone,
            cred.instance_name,
            resp.status_code,
        )
        return {"status": "sent" if resp.status_code < 300 else "failed", "code": resp.status_code}
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
        f"Gym name: {gym_name}\n"
        f"Owner name: {owner_display}"
    )

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
                        },
                    )
                if resp.status_code >= 400:
                    continue
                payload = resp.json() if resp.content else {}
                text = str(payload.get("response") or "").strip()
                if text:
                    return {"text": text, "provider": provider, "model": candidate_model}
            except Exception:
                continue

    fallback = (
        f"Hey {owner_display}! 🎉 Your WhatsApp is now connected to Alfit for {gym_name}. "
        "You are all set to start automations 🚀 Add your first members 👥 and schedule your first broadcast 📣 "
        "to kick things off. Need help? We are here for you 💪"
    )
    return {"text": fallback, "provider": provider or "fallback", "model": model or "template"}


def send_onboarding_self_message(
    db: Session, gym_id: int, phone_number: str | None = None, owner_name: str | None = None
) -> dict:
    """Send a one-time style onboarding welcome to the owner's own WhatsApp number."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        return {"status": "skipped", "reason": "gym_not_found"}

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

    target_phone = (phone_number or "").strip() or (gym.phone or "").strip()
    if not target_phone:
        latest_phone = (
            db.query(GymPhoneNumber)
            .filter(GymPhoneNumber.gym_id == gym_id, GymPhoneNumber.is_active.is_(True))
            .order_by(GymPhoneNumber.id.desc())
            .first()
        )
        if latest_phone:
            target_phone = latest_phone.phone_number

    if not target_phone:
        return {"status": "skipped", "reason": "no_target_phone"}

    ai_copy = _generate_ai_onboarding_copy(gym.name, owner_name)
    payload = {"number": target_phone, "text": ai_copy["text"]}

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{EVOLUTION_API_URL}/message/sendText/{cred.instance_name}",
                headers={"apikey": api_key, "Content-Type": "application/json"},
                json=payload,
            )
        if resp.status_code >= 400:
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
        return {
            "status": "error",
            "reason": str(exc),
            "provider": ai_copy["provider"],
            "model": ai_copy["model"],
        }
