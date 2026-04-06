"""
Bot Configuration
Aqui ficam só as configs que a gente REALMENTE usa no MVP (DeFi + alertas + boletim).
O resto (selenium/indicadores antigos/pagamentos/dca) foi removido pra não poluir nem quebrar deploy.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# TELEGRAM
# ============================================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()

def _parse_int_list(value: str) -> set[int]:
    """Lê IDs separados por vírgula. Ex: '123,456' """
    if not value:
        return set()
    out: set[int] = set()
    for p in [x.strip() for x in value.split(",") if x.strip()]:
        try:
            out.add(int(p))
        except ValueError:
            pass
    return out

ADMIN_USER_IDS = _parse_int_list(os.getenv("ADMIN_USER_IDS", ""))

# Não usamos mais CHAT_ID fixo. Agora é tudo via users.json (chat_id dinâmico).
# CHAT_ID = os.getenv("CHAT_ID", "")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN não configurado em .env")

# ============================================================================
# LOGS (pra debug no deploy)
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# ============================================================================
# DEFI (MVP)
# ============================================================================

DEFI_TOP_LIMIT = int(os.getenv("DEFI_TOP_LIMIT", "5"))
DEFI_APY_MIN = float(os.getenv("DEFI_APY_MIN", "10"))
DEFI_APY_MAX = float(os.getenv("DEFI_APY_MAX", "200"))
DEFI_TVL_MIN = float(os.getenv("DEFI_TVL_MIN", "1000000"))
CHECKOUT_API_URL = os.getenv("CHECKOUT_API_URL", "http://localhost:8000")

# Alertas
APY_JUMP_MIN = float(os.getenv("APY_JUMP_MIN", "10")) 
ALERT_CHECK_MINUTES = int(os.getenv("ALERT_CHECK_MINUTES", "15"))  # produção: 15 min

# ============================================================================
# BOLETIM DIÁRIO (Top pools)
# ============================================================================

# horário local do servidor onde o bot rodar (no deploy a gente ajusta se precisar)
DEFI_DIGEST_HOUR = int(os.getenv("DEFI_DIGEST_HOUR", "9"))
DEFI_DIGEST_MINUTE = int(os.getenv("DEFI_DIGEST_MINUTE", "0"))

# ============================================================================
# FLAGS (opcional)
# ============================================================================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"