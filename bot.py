import logging
import os
import threading

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bhushan Science Bot is alive!", 200


@web_app.route("/health")
def health():
    return {"status": "ok", "bot": "running"}, 200


def run_web():
    port = int(os.environ.get("PORT", "8080"))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧪 Namaste! Main Bhushan Science Bot hoon.\n\n"
        "Science questions poochho ya /help use karo."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📚 Available commands:\n"
        "/start - Bot start karo\n"
        "/help - Help dekho\n"
        "/ping - Bot status check karo\n\n"
        "Aap apna science question normal message mein bhej sakte ho."
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🏓 Pong! Bot online hai.")


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    await update.message.reply_text(
        "🔬 Aapka question mila!\n\n"
        f"“{text}”\n\n"
        "Main Bhushan Science Bot hoon. Is waqt basic bot commands active hain. "
        "Use /help for available commands."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Telegram update error", exc_info=context.error)


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    # Keep the Render health server alive while Telegram polling runs.
    threading.Thread(target=run_web, daemon=True, name="render-web").start()
    log.info("🌐 Render web server started")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.add_error_handler(error_handler)

    log.info("🤖 Bhushan Science Bot starting...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
