from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class SMCSnapshot:
    bos_bull: bool
    bos_bear: bool
    choch_bull: bool
    choch_bear: bool
    near_bullish_ob: bool
    near_bearish_ob: bool
    in_bullish_fvg: bool
    in_bearish_fvg: bool
    structure: str  # bullish / bearish / range


def _swing_points(df: pd.DataFrame, left: int = 2, right: int = 2) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    highs: list[tuple[int, float]] = []
    lows: list[tuple[int, float]] = []
    for i in range(left, len(df) - right):
        window_high = df["high"].iloc[i - left : i + right + 1]
        window_low = df["low"].iloc[i - left : i + right + 1]
        h = float(df["high"].iloc[i])
        l = float(df["low"].iloc[i])
        if h == float(window_high.max()):
            highs.append((i, h))
        if l == float(window_low.min()):
            lows.append((i, l))
    return highs, lows


def _detect_fvg(df: pd.DataFrame) -> tuple[bool, bool]:
    """Check if current price sits in a recent fair value gap."""
    if len(df) < 5:
        return False, False
    price = float(df["close"].iloc[-1])
    in_bull = False
    in_bear = False
    # Look at last 30 candles for unfilled FVGs
    start = max(2, len(df) - 32)
    for i in range(start, len(df) - 1):
        c0_high = float(df["high"].iloc[i - 2])
        c0_low = float(df["low"].iloc[i - 2])
        c2_high = float(df["high"].iloc[i])
        c2_low = float(df["low"].iloc[i])
        # Bullish FVG: gap up between candle0 high and candle2 low
        if c2_low > c0_high:
            if c0_high <= price <= c2_low:
                in_bull = True
        # Bearish FVG: gap down between candle0 low and candle2 high
        if c2_high < c0_low:
            if c2_high <= price <= c0_low:
                in_bear = True
    return in_bull, in_bear


def _order_blocks(df: pd.DataFrame) -> tuple[bool, bool]:
    """Simple OB: last opposite candle before impulsive move, proximity check."""
    if len(df) < 20:
        return False, False
    price = float(df["close"].iloc[-1])
    near_bull = False
    near_bear = False
    lookback = df.iloc[-40:]
    for i in range(2, len(lookback) - 2):
        o = float(lookback["open"].iloc[i])
        c = float(lookback["close"].iloc[i])
        h = float(lookback["high"].iloc[i])
        l = float(lookback["low"].iloc[i])
        next_c = float(lookback["close"].iloc[i + 1])
        next2_c = float(lookback["close"].iloc[i + 2])
        # Bullish OB: bearish candle then strong up
        if c < o and next_c > o and next2_c > next_c:
            if l * 0.998 <= price <= h * 1.002:
                near_bull = True
        # Bearish OB: bullish candle then strong down
        if c > o and next_c < o and next2_c < next_c:
            if l * 0.998 <= price <= h * 1.002:
                near_bear = True
    return near_bull, near_bear


def analyze_smc(df: pd.DataFrame) -> SMCSnapshot | None:
    if len(df) < 50:
        return None

    highs, lows = _swing_points(df)
    if len(highs) < 2 or len(lows) < 2:
        return None

    last_high, prev_high = highs[-1][1], highs[-2][1]
    last_low, prev_low = lows[-1][1], lows[-2][1]
    close = float(df["close"].iloc[-1])

    bos_bull = close > last_high and last_high > prev_high
    bos_bear = close < last_low and last_low < prev_low

    # CHoCH: break against prior structure
    was_bearish = last_high < prev_high and last_low < prev_low
    was_bullish = last_high > prev_high and last_low > prev_low
    choch_bull = was_bearish and close > last_high
    choch_bear = was_bullish and close < last_low

    if last_high > prev_high and last_low > prev_low:
        structure = "bullish"
    elif last_high < prev_high and last_low < prev_low:
        structure = "bearish"
    else:
        structure = "range"

    near_bull_ob, near_bear_ob = _order_blocks(df)
    in_bull_fvg, in_bear_fvg = _detect_fvg(df)

    return SMCSnapshot(
        bos_bull=bos_bull,
        bos_bear=bos_bear,
        choch_bull=choch_bull,
        choch_bear=choch_bear,
        near_bullish_ob=near_bull_ob,
        near_bearish_ob=near_bear_ob,
        in_bullish_fvg=in_bull_fvg,
        in_bearish_fvg=in_bear_fvg,
        structure=structure,
    )
