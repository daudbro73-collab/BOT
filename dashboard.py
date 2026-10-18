"""Dashboard entry-point.

Запускает aiohttp-сервер на :8080 и периодически сканирует Binance SPOT
на волатильные пары. Сигналы передаются в PaperTrader (виртуальный спот).
Все данные транслируются по WebSocket на фронт.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings
from src.analysis.indicators import compute_indicators, ohlcv_to_df
from src.analysis.scorer import build_signal
from src.analysis.smc import analyze_smc
from src.exchange.binance import BinanceClient
from src.exchange.screener import get_volatile_pairs
from src.dashboard.server import DashboardServer
from src.trading.paper_trader import PaperTrader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("dashboard")


async def scan_once(
    client: BinanceClient,
    server: DashboardServer,
    paper: PaperTrader,
) -> None:
    settings = get_settings()
    tfs = list(settings.all_timeframes)
    pairs = await get_volatile_pairs(client)

    pairs_data = [
        {
            "symbol":    p.symbol,
            "last":      p.last,
            "change_24h": round(p.change_pct_24h, 2),
            "volume":    round(p.quote_volume, 0),
            "high":      p.high,
            "low":       p.low,
        }
        for p in pairs[:30]
    ]

    # Обновляем цены в paper-трейдере (закрытие SL/TP)
    price_map = {p.symbol: p.last for p in pairs}
    paper.update_prices(price_map)

    if not pairs:
        await server.broadcast(
            {
                "signals": [],
                "pairs": [],
                "stats": {
                    "total_pairs": 0, "total_signals": 0,
                    "long_count": 0, "short_count": 0,
                    "avg_score": 0, "top_score": 0,
                },
                "paper": paper.snapshot(),
                "ts": time.time(),
                "scan_interval": settings.scan_interval_sec,
            }
        )
        logger.info("No volatile pairs")
        return

    logger.info(
        "Volatile top-%d: %s",
        len(pairs),
        ", ".join(p.symbol for p in pairs[:8]),
    )

    tasks, meta = [], []
    for p in pairs:
        for tf in tfs:
            tasks.append(client.fetch_ohlcv(p.symbol, tf, 200))
            meta.append((p, tf))

    ohlcvs = await asyncio.gather(*tasks, return_exceptions=True)
    signals = []
    for (p, tf), ohlcv in zip(meta, ohlcvs):
        if isinstance(ohlcv, Exception):
            continue
        df  = ohlcv_to_df(ohlcv)
        ind = compute_indicators(df)
        smc = analyze_smc(df)
        if not ind or not smc:
            continue
        sig = build_signal(p.symbol, tf, p.change_pct_24h, ind, smc, df)
        if sig:
            signals.append(sig)
            paper.process_signal(sig)   # виртуальное открытие спот-позиции

    signals.sort(key=lambda s: s.score, reverse=True)

    long_signals  = [s for s in signals if s.side == "LONG"]
    short_signals = [s for s in signals if s.side == "SHORT"]
    signals_data  = [asdict(s) for s in signals[:20]]

    await server.broadcast(
        {
            "signals": signals_data,
            "pairs":   pairs_data,
            "stats": {
                "total_pairs":   len(pairs),
                "total_signals": len(signals),
                "long_count":    len(long_signals),
                "short_count":   len(short_signals),
                "avg_score":     round(
                    sum(s.score for s in signals) / len(signals), 1
                ) if signals else 0,
                "top_score": signals[0].score if signals else 0,
            },
            "paper": paper.snapshot(),
            "ts":           time.time(),
            "scan_interval": settings.scan_interval_sec,
        }
    )

    logger.info(
        "Broadcast: %d signals (L:%d S:%d), %d pairs | "
        "Paper: balance=%.2f pnl=%+.2f open=%d",
        len(signals), len(long_signals), len(short_signals), len(pairs),
        paper.snapshot()["balance"],
        paper.snapshot()["pnl"],
        len(paper.positions),
    )


async def main() -> None:
    settings = get_settings()
    interval = max(15, settings.scan_interval_sec)

    server = DashboardServer()
    runner = await server.start(port=8080)
    logger.info("🚀 Dashboard: http://localhost:8080")

    client = BinanceClient()
    paper  = PaperTrader()
    logger.info("Scanner + PaperTrader started | every %ss", interval)

    try:
        while True:
            started = time.monotonic()
            try:
                await scan_once(client, server, paper)
            except Exception:
                logger.exception("Scan cycle failed")
            elapsed   = time.monotonic() - started
            sleep_for = max(5.0, interval - elapsed)
            logger.info("Next scan in %.0fs", sleep_for)
            await asyncio.sleep(sleep_for)
    finally:
        await client.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
