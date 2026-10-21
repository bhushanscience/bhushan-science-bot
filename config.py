"""Validated configuration for Bhushan Science Bot.

Production secrets belong in the hosting provider's environment variables.
For local development, values may be loaded from a non-committed .env file.
"""
import os
import logging

log = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError:  # Keep startup understandable if the optional loader is absent.
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(override=False)


def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip().strip('"').strip("'")
    return default


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{name} must be a valid integer") from exc
    if value < 0:
        raise RuntimeError(f"{name} cannot be negative")
    return value


BOT_TOKEN = _env_first("BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN")
OWNER_ID = _int_env("OWNER_ID", 0)
DB_FILE = _env_first("DB_FILE", default="bhushan_science.db")
TIMEZONE = _env_first("TIMEZONE", default="Asia/Kolkata")
WEBAPP_URL = _env_first("WEBAPP_URL")
MEME_CHAT_ID = _env_first("MEME_CHAT_ID")
WEBHOOK_SECRET = _env_first("WEBHOOK_SECRET")
EXPECTED_BOT_USERNAME = _env_first("EXPECTED_BOT_USERNAME").lstrip("@").lower()
STICKER_URL = _env_first(
    "STICKER_URL",
    default="https://media.githubusercontent.com/media/ilyhalight/telegram-emoji-effects/master/webp/U+1F389/0.webp",
)
ANIMATION_URL = _env_first("ANIMATION_URL", default="https://i.imgur.com/LyHic3i.gif")

if not BOT_TOKEN:
    log.warning("BOT_TOKEN is not set; bot startup will fail until it is configured.")
