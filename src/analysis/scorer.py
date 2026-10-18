from __future__ import annotations

from dataclasses import dataclass, field

from config import get_settings
from src.analysis.indicators import IndicatorSnapshot, atr
from src.analysis.smc import SMCSnapshot
import pandas as pd


@dataclass
class Signal:
    symbol: str
    timeframe: str
    side: str  # LONG / SHORT
    score: float
    price: float
    change_24h: float
    reasons: list[str] = field(default_factory=list)
    entry: float = 0.0
    sl: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    rr: float = 0.0


def _score_long(ind: IndicatorSnapshot, smc: SMCSnapshot) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    # EMA 25
    if ind.ema_bullish:
        score += 25
        reasons.append("EMA5>21>55")
    elif ind.ema5 > ind.ema21:
        score += 12
        reasons.append("EMA5>EMA21")

    # RSI 20
    if 40 <= ind.rsi <= 55:
        score += 20
        reasons.append(f"RSI reset {ind.rsi:.0f}")
    elif ind.rsi_oversold:
        score += 14
        reasons.append(f"RSI oversold {ind.rsi:.0f}")
    elif ind.rsi < 60:
        score += 6

    # MACD 20
    if ind.macd_bull_cross:
        score += 20
        reasons.append("MACD bull cross")
    elif ind.macd_hist_rising and ind.macd_hist > 0:
        score += 14
        reasons.append("MACD hist rising+")
    elif ind.macd_hist_rising:
        score += 8
        reasons.append("MACD hist rising")

    # SMC 35
    smc_pts = 0.0
    if smc.bos_bull or smc.choch_bull:
        smc_pts += 15
        reasons.append("BOS/CHoCH↑")
    if smc.near_bullish_ob:
        smc_pts += 10
        reasons.append("near bull OB")
    if smc.in_bullish_fvg:
        smc_pts += 6
        reasons.append("in bull FVG")
    if smc.structure == "bullish":
        smc_pts += 4
        reasons.append("bull structure")
    score += min(smc_pts, 35)

    return score, reasons


def _score_short(ind: IndicatorSnapshot, smc: SMCSnapshot) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if ind.ema_bearish:
        score += 25
        reasons.append("EMA5<21<55")
    elif ind.ema5 < ind.ema21:
        score += 12
        reasons.append("EMA5<EMA21")

    if 45 <= ind.rsi <= 60:
        score += 20
        reasons.append(f"RSI fade {ind.rsi:.0f}")
    elif ind.rsi_overbought:
        score += 14
        reasons.append(f"RSI overbought {ind.rsi:.0f}")
    elif ind.rsi > 40:
        score += 6

    if ind.macd_bear_cross:
        score += 20
        reasons.append("MACD bear cross")
    elif ind.macd_hist_falling and ind.macd_hist < 0:
        score += 14
        reasons.append("MACD hist falling-")
    elif ind.macd_hist_falling:
        score += 8
        reasons.append("MACD hist falling")

    smc_pts = 0.0
    if smc.bos_bear or smc.choch_bear:
        smc_pts += 15
        reasons.append("BOS/CHoCH↓")
    if smc.near_bearish_ob:
        smc_pts += 10
        reasons.append("near bear OB")
    if smc.in_bearish_fvg:
        smc_pts += 6
        reasons.append("in bear FVG")
    if smc.structure == "bearish":
        smc_pts += 4
        reasons.append("bear structure")
    score += min(smc_pts, 35)

    return score, reasons


def build_signal(
    symbol: str,
    timeframe: str,
    change_24h: float,
    ind: IndicatorSnapshot,
    smc: SMCSnapshot,
    df: pd.DataFrame,
) -> Signal | None:
    settings = get_settings()
    long_score, long_reasons = _score_long(ind, smc)
    short_score, short_reasons = _score_short(ind, smc)

    if long_score >= short_score:
        side, score, reasons = "LONG", long_score, long_reasons
    else:
        side, score, reasons = "SHORT", short_score, short_reasons

    if score < settings.min_signal_score:
        return None

    price = ind.close
    vol = atr(df) or price * 0.01
    sl_m, tp1_m, tp2_m = settings.atr_sl, settings.atr_tp1, settings.atr_tp2
    if side == "LONG":
        sl = price - sl_m * vol
        tp1 = price + tp1_m * vol
        tp2 = price + tp2_m * vol
        risk = price - sl
        reward = tp1 - price
    else:
        sl = price + sl_m * vol
        tp1 = price - tp1_m * vol
        tp2 = price - tp2_m * vol
        risk = sl - price
        reward = price - tp1

    rr = reward / risk if risk > 0 else 0.0

    return Signal(
        symbol=symbol,
        timeframe=timeframe,
        side=side,
        score=round(score, 1),
        price=price,
        change_24h=change_24h,
        reasons=reasons,
        entry=round(price, 8),
        sl=round(sl, 8),
        tp1=round(tp1, 8),
        tp2=round(tp2, 8),
        rr=round(rr, 2),
    )
