"""
Indicadores (MVP)
- SMA50 x SMA200 no BTC
- detectar cruzamento (Golden/Death) no candle mais recente
"""

import logging
from typing import Dict, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def fetch_btc_history(period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Pega histórico do BTC. 1 ano já cobre SMA200 de boa.
    """
    df = yf.download("BTC-USD", period=period, interval=interval, progress=False)
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()


def detect_ma_cross_btc() -> Optional[Dict]:
    """
    Detecta cruzamento SMA50 x SMA200 no candle mais recente.

    Retorna um dict quando cruzou AGORA (no último candle).
    Se não cruzou, retorna None.

    type:
      - golden_cross: SMA50 cruza pra cima da SMA200
      - death_cross:  SMA50 cruza pra baixo da SMA200
    """
    try:
        df = fetch_btc_history()

        if df.empty or "Close" not in df:
            return None

        close = df["Close"].dropna()
        if len(close) < 210:
            return None

        sma50 = _sma(close, 50)
        sma200 = _sma(close, 200)

        # comparação dos últimos 2 candles pra saber se cruzou agora
        prev_diff = float(sma50.iloc[-2] - sma200.iloc[-2])
        curr_diff = float(sma50.iloc[-1] - sma200.iloc[-1])

        # Golden cross
        if prev_diff <= 0 and curr_diff > 0:
            return {
                "type": "golden_cross",
                "symbol": "BTC-USD",
                "close": float(close.iloc[-1]),
                "sma50": float(sma50.iloc[-1]),
                "sma200": float(sma200.iloc[-1]),
            }

        # Death cross
        if prev_diff >= 0 and curr_diff < 0:
            return {
                "type": "death_cross",
                "symbol": "BTC-USD",
                "close": float(close.iloc[-1]),
                "sma50": float(sma50.iloc[-1]),
                "sma200": float(sma200.iloc[-1]),
            }

        return None

    except Exception as e:
        logger.error(f"Erro no detect_ma_cross_btc: {e}", exc_info=True)
        return None