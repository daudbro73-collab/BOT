from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict

from aiogram import Bot

from config import get_settings
from src.analysis.indicators import compute_indicators, ohlcv_to_df
from src.analysis.scorer import Signal, build_signal
from src.analysis.smc import analyze_smc
from src.bot.formatting import format_signal
from src.exchange.binance import BinanceClient
from src.exchange.screener import get_volatile_pairs
from src.trading.paper_trader import PaperTrader
from src.storage.users import UserStore

logger = logging.getLogger(__name__)


class ScannerEngine:
    def __init__(self, bot: Bot, users: UserStore) -> None:
        self.bot = bot
        self.users = users
        self.client = BinanceClient()
        self._running = False
        self._task: asyncio.Task | None = None
        # dedupe: symbol:tf:side -> last sent ts
        self._sent: dict[str, float] = {}
        self._cooldown_sec = 30 * 60
        self.paper_trader = PaperTrader()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="scanner")
        logger.info("Scanner started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self.client.close()
        logger.info("Scanner stopped")

    async def _loop(self) -> None:
        settings = get_settings()
        while self._running:
            started = time.monotonic()
            try:
                await self._scan_once()
            except Exception:
                logger.exception("Scan cycle failed")
            elapsed = time.monotonic() - started
            sleep_for = max(5.0, settings.scan_interval_sec - elapsed)
            await asyncio.sleep(sleep_for)

    def _should_send(self, signal: Signal) -> bool:
        key = f"{signal.symbol}:{signal.timeframe}:{signal.side}"
        now = time.time()
        last = self._sent.get(key, 0)
        if now - last < self._cooldown_sec:
            return False
        self._sent[key] = now
        return True

    async def _analyze_pair_tf(
        self,
        symbol: str,
        timeframe: str,
        change_24h: float,
    ) -> Signal | None:
        try:
            ohlcv = await self.client.fetch_ohlcv(symbol, timeframe, limit=200)
            df = ohlcv_to_df(ohlcv)
            ind = compute_indicators(df)
            smc = analyze_smc(df)
            if not ind or not smc:
                return None
            return build_signal(symbol, timeframe, change_24h, ind, smc, df)
        except Exception:
            logger.exception("Analyze failed %s %s", symbol, timeframe)
            return None

    async def _scan_once(self) -> None:
        settings = get_settings()
        active = await self.users.active_users()
        if not active:
            logger.info("No active subscribers, skip scan")
            return

        # Union of all requested timeframes
        needed_tfs: set[str] = set()
        for u in active:
            needed_tfs.update(u.normalized_tfs(settings.all_timeframes))
        if not needed_tfs:
            return

        pairs = await get_volatile_pairs(self.client)
        if not pairs:
            logger.info("No volatile pairs matched filters")
            return

        logger.info("Scanning %d pairs x %s", len(pairs), sorted(needed_tfs))

        tasks = [
            self._analyze_pair_tf(p.symbol, tf, p.change_pct_24h)
            for p in pairs
            for tf in needed_tfs
        ]
        results = await asyncio.gather(*tasks)
        signals = [s for s in results if s is not None]

        # Group by timeframe for user filtering
        by_tf: dict[str, list[Signal]] = defaultdict(list)
        for s in signals:
            if self._should_send(s):
                by_tf[s.timeframe].append(s)

        if not by_tf:
            logger.info("No new signals this cycle")
            return

        for user in active:
            user_tfs = set(user.normalized_tfs(settings.all_timeframes))
            min_score = user.min_score if user.min_score is not None else settings.min_signal_score
            to_send: list[Signal] = []
            for tf, items in by_tf.items():
                if tf not in user_tfs:
                    continue
                to_send.extend(s for s in items if s.score >= min_score)

            # Cap spam: top 5 by score per user per cycle
            to_send.sort(key=lambda x: x.score, reverse=True)
            for signal in to_send[:5]:
                self.paper_trader.process_signal(signal)
                try:
                    await self.bot.send_message(
                        chat_id=user.user_id,
                        text=format_signal(signal),
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                except Exception:
                    logger.exception("Failed to send to %s", user.user_id)
