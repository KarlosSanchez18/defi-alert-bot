import time
import requests
from typing import Any, Dict, List, Optional

from config import (
    DEFI_APY_MIN,
    DEFI_APY_MAX,
    DEFI_TVL_MIN,
    DEFI_TOP_LIMIT,
)

URL = "https://yields.llama.fi/pools"

# reaproveita conexão (melhor e mais rápido que requests.get toda hora)
_session = requests.Session()
_session.headers.update({"User-Agent": "defi-alert-bot/1.0"})

ALLOWED_PROJECTS = {
    "uniswap-v3",
    "uniswap-v2",
    "curve",
    "aave-v3",
    "aave-v2",
    "balancer-v2",
    "raydium-amm",
    "pancakeswap-v3",
    "pancakeswap-v2",
}


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_pools(timeout: int = 12, retries: int = 2, backoff_seconds: float = 1.5) -> List[Dict[str, Any]]:
    last_err: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            resp = _session.get(URL, timeout=timeout)
            resp.raise_for_status()

            data = resp.json()
            pools = data.get("data", [])
            return pools if isinstance(pools, list) else []

        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)

    # se falhar tudo, estoura o último erro
    raise last_err if last_err else RuntimeError("Falha desconhecida ao buscar pools da DefiLlama")


def filter_pools(pools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []

    for p in pools:
        apy = _safe_float(p.get("apy"))
        tvl = _safe_float(p.get("tvlUsd"))
        symbol = (p.get("symbol") or "").strip()
        project = (p.get("project") or "").strip()
        chain = (p.get("chain") or "").strip()

        if apy is None or tvl is None or not symbol or not project or not chain:
            continue

        if project not in ALLOWED_PROJECTS:
            continue

        if apy < DEFI_APY_MIN:
            continue
        if apy > DEFI_APY_MAX:
            continue
        if tvl < DEFI_TVL_MIN:
            continue

        filtered.append(p)

    return filtered


def top_pools(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if limit is None:
        limit = DEFI_TOP_LIMIT

    pools = fetch_pools()
    pools = filter_pools(pools)

    pools_sorted = sorted(pools, key=lambda x: float(x.get("apy") or 0.0), reverse=True)
    return pools_sorted[: int(limit)]