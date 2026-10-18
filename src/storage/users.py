from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from config import get_settings


@dataclass
class UserPrefs:
    user_id: int
    active: bool = True
    timeframes: list[str] = field(default_factory=list)
    min_score: float | None = None

    def normalized_tfs(self, allowed: Iterable[str]) -> list[str]:
        allowed_set = set(allowed)
        return [tf for tf in self.timeframes if tf in allowed_set]


class UserStore:
    """Simple JSON persistence for per-user preferences."""

    def __init__(self, path: str | Path | None = None) -> None:
        settings = get_settings()
        self.path = Path(path or settings.users_db_path)
        self._lock = asyncio.Lock()
        self._users: dict[int, UserPrefs] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._users = {}
            return
        raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        self._users = {
            int(uid): UserPrefs(
                user_id=int(uid),
                active=bool(data.get("active", True)),
                timeframes=list(data.get("timeframes") or []),
                min_score=data.get("min_score"),
            )
            for uid, data in raw.items()
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {str(uid): asdict(prefs) for uid, prefs in self._users.items()}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    async def get_or_create(self, user_id: int) -> UserPrefs:
        settings = get_settings()
        async with self._lock:
            if user_id not in self._users:
                self._users[user_id] = UserPrefs(
                    user_id=user_id,
                    active=True,
                    timeframes=list(settings.default_tf_list),
                )
                self._save()
            return self._users[user_id]

    async def set_active(self, user_id: int, active: bool) -> UserPrefs:
        prefs = await self.get_or_create(user_id)
        async with self._lock:
            prefs.active = active
            self._save()
            return prefs

    async def set_timeframes(self, user_id: int, timeframes: list[str]) -> UserPrefs:
        settings = get_settings()
        allowed = set(settings.all_timeframes)
        clean = [tf for tf in timeframes if tf in allowed]
        if not clean:
            raise ValueError(f"Нужен хотя бы один TF из: {', '.join(settings.all_timeframes)}")
        prefs = await self.get_or_create(user_id)
        async with self._lock:
            prefs.timeframes = clean
            self._save()
            return prefs

    async def active_users(self) -> list[UserPrefs]:
        async with self._lock:
            return [u for u in self._users.values() if u.active]
