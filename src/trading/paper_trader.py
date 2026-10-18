"""Spot paper-trading simulator.

Каждый сигнал открывает виртуальную LONG-позицию на споте.
SHORT-сигналы игнорируются (спот не поддерживает короткие позиции).
Позиция закрывается автоматически при достижении SL, TP1 или TP2.
Все события логируются в data/paper_logs.csv.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.analysis.scorer import Signal

logger = logging.getLogger(__name__)

VIRTUAL_BALANCE_USDT = 1000.0   # стартовый виртуальный баланс
RISK_PER_TRADE_PCT   = 0.02      # 2 % баланса на сделку
MAX_OPEN_POSITIONS   = 5         # максимум одновременных позиций
LOG_PATH             = Path("data/paper_logs.csv")

CSV_HEADER = [
    "timestamp", "event",
    "symbol", "timeframe", "side",
    "entry", "sl", "tp1", "tp2",
    "qty", "exit_price", "pnl_usdt", "balance",
    "score", "reasons",
]


@dataclass
class Position:
    symbol:    str
    timeframe: str
    entry:     float
    sl:        float
    tp1:       float
    tp2:       float
    qty:       float          # кол-во базовой монеты
    opened_at: str = ""
    score:     float = 0.0
    reasons:   list[str] = field(default_factory=list)
    hit_tp1:   bool = False   # уже взяли TP1 (50 % позиции)

    @property
    def cost_usdt(self) -> float:
        return self.entry * self.qty


class PaperTrader:
    """Spot-only виртуальный трейдер."""

    def __init__(self) -> None:
        self.balance: float = VIRTUAL_BALANCE_USDT
        self.positions: dict[str, Position] = {}   # symbol -> Position
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.total_pnl: float = 0.0
        self._ensure_log()

    # ── public API ──────────────────────────────────────────────────────────

    def process_signal(self, signal: Signal) -> None:
        """Принять сигнал: открыть позицию (только LONG на споте)."""
        if signal.side != "LONG":
            return                          # спот — только лонги
        if signal.symbol in self.positions:
            return                          # уже в позиции
        if len(self.positions) >= MAX_OPEN_POSITIONS:
            logger.info("PaperTrader: max positions reached, skip %s", signal.symbol)
            return
        if signal.sl <= 0 or signal.entry <= 0:
            return

        risk_usdt = self.balance * RISK_PER_TRADE_PCT
        risk_per_unit = signal.entry - signal.sl
        if risk_per_unit <= 0:
            return

        qty = risk_usdt / risk_per_unit
        cost = qty * signal.entry
        if cost > self.balance:
            qty = self.balance * 0.95 / signal.entry  # не тратим больше баланса

        pos = Position(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            entry=signal.entry,
            sl=signal.sl,
            tp1=signal.tp1,
            tp2=signal.tp2,
            qty=round(qty, 6),
            opened_at=_now(),
            score=signal.score,
            reasons=signal.reasons,
        )
        self.positions[signal.symbol] = pos
        self._log("OPEN", pos)
        logger.info(
            "PaperTrader OPEN  %s @ %.6f  qty=%.4f  cost=%.2f USDT",
            pos.symbol, pos.entry, pos.qty, pos.cost_usdt,
        )

    def update_prices(self, prices: dict[str, float]) -> None:
        """Обновить цены и закрыть позиции по SL/TP."""
        for symbol, price in prices.items():
            pos = self.positions.get(symbol)
            if pos is None:
                continue

            # SL hit
            if price <= pos.sl:
                self._close(pos, price, "SL")

            # TP1 hit (закрываем 50 %, оставляем на TP2)
            elif not pos.hit_tp1 and price >= pos.tp1:
                half_qty = pos.qty / 2
                pnl = (price - pos.entry) * half_qty
                self.balance += pnl
                self.total_pnl += pnl
                self.total_trades += 1
                self.winning_trades += 1
                pos.qty -= half_qty
                pos.hit_tp1 = True
                self._log("TP1", pos, exit_price=price, pnl=pnl)
                logger.info("PaperTrader TP1   %s @ %.6f  pnl=+%.2f", symbol, price, pnl)

            # TP2 hit (закрываем остаток)
            elif pos.hit_tp1 and price >= pos.tp2:
                self._close(pos, price, "TP2")

    def snapshot(self) -> dict:
        """Текущее состояние для дашборда."""
        return {
            "balance": round(self.balance, 2),
            "pnl": round(self.total_pnl, 2),
            "total_trades": self.total_trades,
            "win_rate": round(self.winning_trades / self.total_trades * 100, 1)
                        if self.total_trades else 0.0,
            "open_positions": [
                {
                    "symbol":    p.symbol,
                    "timeframe": p.timeframe,
                    "entry":     p.entry,
                    "sl":        p.sl,
                    "tp1":       p.tp1,
                    "tp2":       p.tp2,
                    "qty":       p.qty,
                    "opened_at": p.opened_at,
                    "score":     p.score,
                    "hit_tp1":   p.hit_tp1,
                }
                for p in self.positions.values()
            ],
        }

    # ── internals ───────────────────────────────────────────────────────────

    def _close(self, pos: Position, exit_price: float, reason: str) -> None:
        pnl = (exit_price - pos.entry) * pos.qty
        self.balance += pnl
        self.total_pnl += pnl
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        self._log(reason, pos, exit_price=exit_price, pnl=pnl)
        del self.positions[pos.symbol]
        logger.info(
            "PaperTrader %-4s  %s @ %.6f  pnl=%+.2f  balance=%.2f",
            reason, pos.symbol, exit_price, pnl, self.balance,
        )

    def _log(
        self,
        event: str,
        pos: Position,
        exit_price: float = 0.0,
        pnl: float = 0.0,
    ) -> None:
        row = [
            _now(), event,
            pos.symbol, pos.timeframe, "LONG",
            pos.entry, pos.sl, pos.tp1, pos.tp2,
            pos.qty,
            exit_price if exit_price else "",
            round(pnl, 4) if event != "OPEN" else "",
            round(self.balance, 2),
            pos.score,
            "; ".join(pos.reasons),
        ]
        with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

    def _ensure_log(self) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not LOG_PATH.is_file():
            with LOG_PATH.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(CSV_HEADER)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
