import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

SUBSCRIBERS_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")


def load_subscribers() -> List[Dict[str, Any]]:
    """Carrega assinantes do arquivo. Se não existir ou estiver ruim, retorna []."""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []

    try:
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_subscribers(subscribers: List[Dict[str, Any]]) -> None:
    """Salva assinantes de forma atômica."""
    folder = os.path.dirname(SUBSCRIBERS_FILE)
    os.makedirs(folder, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix="subscribers_", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, SUBSCRIBERS_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def add_subscriber(
    telegram_user_id: int,
    chat_id: Optional[int] = None,
    email: Optional[str] = None,
    plan: str = "monthly",
    status: str = "active",
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
) -> None:
    """
    Adiciona ou atualiza um assinante.
    """
    subscribers = load_subscribers()
    now = datetime.utcnow().isoformat()

    for s in subscribers:
        if s.get("telegram_user_id") == telegram_user_id:
            s["status"] = status
            s["plan"] = plan
            if chat_id is not None:
                s["chat_id"] = chat_id
            if email is not None:
                s["email"] = email
            if stripe_customer_id is not None:
                s["stripe_customer_id"] = stripe_customer_id
            if stripe_subscription_id is not None:
                s["stripe_subscription_id"] = stripe_subscription_id
            s["updated_at"] = now
            save_subscribers(subscribers)
            return

    subscribers.append({
        "telegram_user_id": telegram_user_id,
        "chat_id": chat_id,
        "email": email,
        "plan": plan,
        "status": status,
        "stripe_customer_id": stripe_customer_id,
        "stripe_subscription_id": stripe_subscription_id,
        "created_at": now,
    })
    save_subscribers(subscribers)


def is_subscriber(telegram_user_id: int) -> bool:
    """Retorna True se o usuário tiver assinatura ativa."""
    subscribers = load_subscribers()

    for s in subscribers:
        if (
            s.get("telegram_user_id") == telegram_user_id
            and s.get("status") == "active"
        ):
            return True

    return False


def remove_subscriber(telegram_user_id: int) -> bool:
    """
    Remove assinante pelo telegram_user_id.
    Retorna True se removeu, False se não encontrou.
    """
    subscribers = load_subscribers()
    new_subscribers = [s for s in subscribers if s.get("telegram_user_id") != telegram_user_id]

    if len(new_subscribers) == len(subscribers):
        return False

    save_subscribers(new_subscribers)
    return True


def deactivate_subscriber(telegram_user_id: int) -> bool:
    """
    Marca assinante como inativo.
    Retorna True se encontrou, False se não encontrou.
    """
    subscribers = load_subscribers()
    now = datetime.utcnow().isoformat()

    for s in subscribers:
        if s.get("telegram_user_id") == telegram_user_id:
            s["status"] = "inactive"
            s["updated_at"] = now
            save_subscribers(subscribers)
            return True

    return False


def list_subscribers() -> List[Dict[str, Any]]:
    """Lista todos os assinantes."""
    return load_subscribers()