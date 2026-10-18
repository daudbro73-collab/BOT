from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from config import get_settings
from src.storage.users import UserStore

router = Router()


def _status_text(prefs) -> str:
    settings = get_settings()
    state = "🟢 ON" if prefs.active else "🔴 OFF"
    tfs = ", ".join(prefs.timeframes) or "—"
    score = prefs.min_score if prefs.min_score is not None else settings.min_signal_score
    return (
        f"<b>Статус</b>\n"
        f"Сигналы: {state}\n"
        f"Таймфреймы: <code>{tfs}</code>\n"
        f"Min score: <code>{score}</code>\n"
        f"Доступные TF: <code>{', '.join(settings.all_timeframes)}</code>"
    )


@router.message(Command("start"))
async def cmd_start(message: Message, users: UserStore) -> None:
    prefs = await users.set_active(message.from_user.id, True)
    settings = get_settings()
    if not prefs.timeframes:
        prefs = await users.set_timeframes(message.from_user.id, list(settings.default_tf_list))

    await message.answer(
        "Привет. Я сканирую волатильные USDT-пары Binance Spot за 24ч,\n"
        "считаю EMA 5/21/55, RSI, MACD и Smart Money, и шлю только сигналы.\n\n"
        "Команды:\n"
        "/start — включить сигналы\n"
        "/stop — выключить сигналы\n"
        "/timeframe 1m 5m 15m 1h — выбрать TF\n"
        "/status — текущие настройки\n\n"
        + _status_text(prefs),
        parse_mode="HTML",
    )


@router.message(Command("stop"))
async def cmd_stop(message: Message, users: UserStore) -> None:
    prefs = await users.set_active(message.from_user.id, False)
    await message.answer("Сигналы выключены.\n\n" + _status_text(prefs), parse_mode="HTML")


@router.message(Command("status"))
async def cmd_status(message: Message, users: UserStore) -> None:
    prefs = await users.get_or_create(message.from_user.id)
    await message.answer(_status_text(prefs), parse_mode="HTML")


@router.message(Command("timeframe"))
async def cmd_timeframe(message: Message, command: CommandObject, users: UserStore) -> None:
    settings = get_settings()
    args = (command.args or "").strip().lower().replace(",", " ").split()
    if not args:
        await message.answer(
            "Укажи таймфреймы через пробел.\n"
            f"Пример: <code>/timeframe 5m 15m 1h</code>\n"
            f"Доступно: <code>{', '.join(settings.all_timeframes)}</code>",
            parse_mode="HTML",
        )
        return

    # normalize aliases
    aliases = {"1": "1m", "5": "5m", "1m": "1m", "5m": "5m"}
    normalized = []
    for a in args:
        tf = aliases.get(a, a)
        normalized.append(tf)

    try:
        prefs = await users.set_timeframes(message.from_user.id, normalized)
    except ValueError as e:
        await message.answer(str(e))
        return

    await message.answer("Таймфреймы обновлены.\n\n" + _status_text(prefs), parse_mode="HTML")
