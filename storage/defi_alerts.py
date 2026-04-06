import json
import os
import tempfile
from typing import Any, Dict, List, Tuple

SNAPSHOT_FILE = os.path.join(os.path.dirname(__file__), "defi_snapshot.json")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_snapshot() -> Dict[str, Dict[str, Any]]:
    """Carrega o snapshot do disco. Se não existir ou estiver corrompido, retorna {}."""
    if not os.path.exists(SNAPSHOT_FILE):
        return {}

    try:
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_snapshot(snapshot: Dict[str, Dict[str, Any]]) -> None:
    """Salva snapshot de forma atômica (evita corromper o arquivo se cair no meio)."""
    folder = os.path.dirname(SNAPSHOT_FILE)
    os.makedirs(folder, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix="defi_snapshot_", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, SNAPSHOT_FILE)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def pool_key(pool: Dict[str, Any]) -> str:
    """Chave estável para identificar uma pool entre execuções."""
    chain = str(pool.get("chain") or "").strip()
    project = str(pool.get("project") or "").strip()
    symbol = str(pool.get("symbol") or "").strip()
    return f"{chain}-{project}-{symbol}"


def build_snapshot(pools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Cria snapshot no formato: { pool_key: { 'apy': float } }"""
    snap: Dict[str, Dict[str, Any]] = {}
    for p in pools:
        snap[pool_key(p)] = {"apy": _safe_float(p.get("apy"), 0.0)}
    return snap


def diff_pools(
    current_pools: List[Dict[str, Any]],
    old_snapshot: Dict[str, Dict[str, Any]],
    apy_jump_min: float = 10.0,
) -> Tuple[List[Dict[str, Any]], List[Tuple[Dict[str, Any], float, float]]]:
    """
    Retorna:
    - new_pools: pools novas que não existiam no snapshot
    - apy_jumps: lista (pool, old_apy, new_apy) quando subiu >= apy_jump_min
    """
    new_pools: List[Dict[str, Any]] = []
    apy_jumps: List[Tuple[Dict[str, Any], float, float]] = []

    for p in current_pools:
        key = pool_key(p)
        apy = _safe_float(p.get("apy"), 0.0)

        if key not in old_snapshot:
            new_pools.append(p)
            continue

        old_apy = _safe_float(old_snapshot[key].get("apy"), 0.0)
        if (apy - old_apy) >= float(apy_jump_min):
            apy_jumps.append((p, old_apy, apy))

    return new_pools, apy_jumps