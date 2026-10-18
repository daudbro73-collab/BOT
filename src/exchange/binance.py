from __future__ import annotations

from dataclasses import dataclass

import ccxt.async_support as ccxt

from config import get_settings


TF_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
}


@dataclass
class TickerStats:
    symbol: str
    last: float
    change_pct_24h: float
    quote_volume: float
    high: float
    low: float


class BinanceClient:
    def __init__(self) -> None:
        settings = get_settings()
        # data-api.binance.vision — публичный market-data endpoint (удобно при geo-block api.binance.com)
        hostname = (settings.binance_hostname or "data-api.binance.vision").strip()
        self.exchange = ccxt.binance(
            {
                "apiKey": settings.binance_api_key or None,
                "secret": settings.binance_api_secret or None,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",
                    "fetchMarkets": ["spot"],
                },
            }
        )
        api_urls = self.exchange.urls.get("api", {})
        if isinstance(api_urls, dict):
            api_urls["public"] = f"https://{hostname}/api/v3"
            api_urls["private"] = f"https://{hostname}/api/v3"
            api_urls["v1"] = f"https://{hostname}/api/v1"
            self.exchange.urls["api"] = api_urls

    async def close(self) -> None:
        await self.exchange.close()

    async def fetch_usdt_tickers(self) -> list[TickerStats]:
        tickers = await self.exchange.fetch_tickers()
        result: list[TickerStats] = []
        for symbol, t in tickers.items():
            if not symbol.endswith("/USDT"):
                continue
            base = symbol.split("/")[0]
            # Skip leveraged tokens / stables
            if base.endswith(("UP", "DOWN")) or base.endswith(("BULL", "BEAR")):
                continue
            if base in {"USDC", "BUSD", "TUSD", "FDUSD", "DAI", "EUR", "AEUR"}:
                continue
            change = t.get("percentage")
            quote_vol = t.get("quoteVolume")
            last = t.get("last")
            if change is None or quote_vol is None or last is None:
                continue
            result.append(
                TickerStats(
                    symbol=symbol,
                    last=float(last),
                    change_pct_24h=float(change),
                    quote_volume=float(quote_vol),
                    high=float(t.get("high") or last),
                    low=float(t.get("low") or last),
                )
            )
        return result

    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> list[list[float]]:
        tf = TF_MAP[timeframe]
        return await self.exchange.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
