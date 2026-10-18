from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD


@dataclass
class IndicatorSnapshot:
    close: float
    ema5: float
    ema21: float
    ema55: float
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    macd_hist_prev: float
    ema_bullish: bool
    ema_bearish: bool
    rsi_oversold: bool
    rsi_overbought: bool
    macd_bull_cross: bool
    macd_bear_cross: bool
    macd_hist_rising: bool
    macd_hist_falling: bool


def ohlcv_to_df(ohlcv: list[list[float]]) -> pd.DataFrame:
    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df


def compute_indicators(df: pd.DataFrame) -> IndicatorSnapshot | None:
    if len(df) < 60:
        return None

    close = df["close"]
    ema5 = EMAIndicator(close, window=5).ema_indicator()
    ema21 = EMAIndicator(close, window=21).ema_indicator()
    ema55 = EMAIndicator(close, window=55).ema_indicator()
    rsi = RSIIndicator(close, window=14).rsi()
    macd_ind = MACD(close, window_slow=26, window_fast=12, window_sign=9)

    i = -1
    e5, e21, e55 = float(ema5.iloc[i]), float(ema21.iloc[i]), float(ema55.iloc[i])
    rsi_v = float(rsi.iloc[i])
    macd_v = float(macd_ind.macd().iloc[i])
    macd_sig = float(macd_ind.macd_signal().iloc[i])
    macd_hist = float(macd_ind.macd_diff().iloc[i])
    macd_hist_prev = float(macd_ind.macd_diff().iloc[i - 1])

    macd_prev = float(macd_ind.macd().iloc[i - 1])
    macd_sig_prev = float(macd_ind.macd_signal().iloc[i - 1])

    return IndicatorSnapshot(
        close=float(close.iloc[i]),
        ema5=e5,
        ema21=e21,
        ema55=e55,
        rsi=rsi_v,
        macd=macd_v,
        macd_signal=macd_sig,
        macd_hist=macd_hist,
        macd_hist_prev=macd_hist_prev,
        ema_bullish=e5 > e21 > e55,
        ema_bearish=e5 < e21 < e55,
        rsi_oversold=rsi_v <= 35,
        rsi_overbought=rsi_v >= 65,
        macd_bull_cross=macd_prev <= macd_sig_prev and macd_v > macd_sig,
        macd_bear_cross=macd_prev >= macd_sig_prev and macd_v < macd_sig,
        macd_hist_rising=macd_hist > macd_hist_prev,
        macd_hist_falling=macd_hist < macd_hist_prev,
    )


def atr(df: pd.DataFrame, period: int = 14) -> float:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])
