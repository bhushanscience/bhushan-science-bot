import os
import threading

from flask import Flask
from telegram.ext import Application

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Bhushan Science Bot is alive!"


def run_web():
    port = int(os.environ.get("PORT", "8080"))
    web_app.run(host="0.0.0.0", port=port)


def main():
    threading.Thread(target=run_web, daemon=True).start()

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    app = Application.builder().token(BOT_TOKEN).build()
    app.run_polling()


if __name__ == "__main__":
    main()
