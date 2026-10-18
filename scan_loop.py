from __future__ import annotations

import asyncio
import logging
import sys
import time
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("scan_loop")


async def scan_once(client: BinanceClient) -> None:
    settings = get_settings()
    tfs = list(settings.all_timeframes)
    pairs = await get_volatile_pairs(client)
    if not pairs:
        logger.info("No volatile pairs")
        return

    logger.info("Volatile top-%d: %s", len(pairs), ", ".join(p.symbol for p in pairs[:8]))

    tasks = []
    meta = []
    for p in pairs:
        for tf in tfs:
            tasks.append(client.fetch_ohlcv(p.symbol, tf, 200))
            meta.append((p, tf))

    ohlcvs = await asyncio.gather(*tasks, return_exceptions=True)
    signals = []
    for (p, tf), ohlcv in zip(meta, ohlcvs):
        if isinstance(ohlcv, Exception):
            continue
        df = ohlcv_to_df(ohlcv)
        ind = compute_indicators(df)
        smc = analyze_smc(df)
        if not ind or not smc:
            continue
        sig = build_signal(p.symbol, tf, p.change_pct_24h, ind, smc, df)
        if sig:
            signals.append(sig)

    signals.sort(key=lambda s: s.score, reverse=True)
    logger.info("Signals >= %.0f: %d (pairs=%d x tf=%s)", settings.min_signal_score, len(signals), len(pairs), tfs)

    for s in signals[:15]:
        print(
            f"  {s.side:5} {s.symbol:14} TF={s.timeframe:3} "
            f"score={s.score:5.1f} 24h={s.change_24h:+.1f}%  "
            f"entry={s.entry}  SL={s.sl}  TP1={s.tp1}  | {', '.join(s.reasons[:4])}"
        )
    if not signals:
        print("  (нет сигналов выше порога)")


async def main() -> None:
    settings = get_settings()
    interval = max(15, settings.scan_interval_sec)
    client = BinanceClient()
    logger.info("Terminal scanner started | every %ss | no Telegram", interval)
    try:
        while True:
            started = time.monotonic()
            try:
                await scan_once(client)
            except Exception:
                logger.exception("Scan cycle failed")
            elapsed = time.monotonic() - started
            sleep_for = max(5.0, interval - elapsed)
            logger.info("Next scan in %.0fs", sleep_for)
            await asyncio.sleep(sleep_for)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
