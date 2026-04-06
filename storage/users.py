import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users() -> List[Dict[str, Any]]:
    """Carrega usuários do arquivo. Se não existir ou estiver ruim, retorna []."""
    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_users(users: List[Dict[str, Any]]) -> None:
    """Salva usuários de forma atômica (evita corromper se cair no meio)."""
    folder = os.path.dirname(USERS_FILE)
    os.makedirs(folder, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix="users_", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, USERS_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def add_user(telegram_user_id: int, chat_id: int) -> None:
    """
    Adiciona usuário novo.
    - Se já existir, não duplica.
    - Se o chat_id mudou (raro, mas pode acontecer), atualiza.
    """
    users = load_users()
    now = datetime.utcnow().isoformat()

    for u in users:
        if u.get("telegram_user_id") == telegram_user_id:
            # atualiza chat_id se mudou
            if u.get("chat_id") != chat_id:
                u["chat_id"] = chat_id
                u["updated_at"] = now
                save_users(users)
            return

    users.append({
        "telegram_user_id": telegram_user_id,
        "chat_id": chat_id,
        "created_at": now
    })
    save_users(users)


def list_users() -> List[Dict[str, Any]]:
    """Lista todos usuários (mesmo que load_users)."""
    return load_users()