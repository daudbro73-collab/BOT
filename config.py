from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str

    binance_api_key: str = ""
    binance_api_secret: str = ""
    # Public market data host. Default works better when api.binance.com is geo-blocked.
    binance_hostname: str = "data-api.binance.vision"

    scan_interval_sec: int = 30
    top_volatile: int = 30
    min_24h_change_pct: float = 5.0
    min_quote_volume_usdt: float = 5_000_000
    min_signal_score: float = 70.0

    default_timeframes: str = "1m,5m"

    # Scalp-only timeframes
    all_timeframes: tuple[str, ...] = ("1m", "5m")

    # ATR multipliers for SL/TP (tighter = scalping)
    atr_sl: float = 1.0
    atr_tp1: float = 1.5
    atr_tp2: float = 2.5

    users_db_path: str = "data/users.json"

    @property
    def default_tf_list(self) -> list[str]:
        return [tf.strip() for tf in self.default_timeframes.split(",") if tf.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
