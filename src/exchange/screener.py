from __future__ import annotations

from config import get_settings
from src.exchange.binance import BinanceClient, TickerStats


def screen_volatile(tickers: list[TickerStats]) -> list[TickerStats]:
    settings = get_settings()
    filtered = [
        t
        for t in tickers
        if abs(t.change_pct_24h) >= settings.min_24h_change_pct
        and t.quote_volume >= settings.min_quote_volume_usdt
    ]
    filtered.sort(key=lambda x: abs(x.change_pct_24h), reverse=True)
    return filtered[: settings.top_volatile]


async def get_volatile_pairs(client: BinanceClient) -> list[TickerStats]:
    tickers = await client.fetch_usdt_tickers()
    return screen_volatile(tickers)
