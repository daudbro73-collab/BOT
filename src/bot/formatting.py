from __future__ import annotations

from src.analysis.scorer import Signal


def format_signal(s: Signal) -> str:
    emoji = "🟢" if s.side == "LONG" else "🔴"
    change = f"{s.change_24h:+.2f}%"
    reasons = ", ".join(s.reasons[:6]) or "confluence"
    chart = f"https://www.binance.com/en/trade/{s.symbol.replace('/', '_')}?type=spot"

    return (
        f"{emoji} <b>{s.side}</b> | <code>{s.symbol}</code>\n"
        f"TF: <b>{s.timeframe}</b> | Score: <b>{s.score}</b>\n"
        f"24h: {change}\n\n"
        f"Setup: {reasons}\n"
        f"Entry: <code>{_fmt(s.entry)}</code>\n"
        f"SL: <code>{_fmt(s.sl)}</code>\n"
        f"TP1: <code>{_fmt(s.tp1)}</code> | TP2: <code>{_fmt(s.tp2)}</code>\n"
        f"R:R ≈ {s.rr}\n\n"
        f"<a href=\"{chart}\">Binance chart</a>"
    )


def _fmt(v: float) -> str:
    if v >= 1000:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:.4f}"
    return f"{v:.8f}".rstrip("0").rstrip(".")
