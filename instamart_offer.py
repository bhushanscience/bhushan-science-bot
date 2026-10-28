"""Telegram Instamart offer calculator; local estimates only."""
import json
import logging
import math
from datetime import datetime
from pathlib import Path
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)
TARGET_DISCOUNT = 300.00
REPORT_FILE = Path("instamart_offer_report.json")

async def instamart_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting"] = "instamart_cart"
    context.user_data["instamart_values"] = {}
    await update.effective_message.reply_text(
        "🛒 <b>Instamart Offer Checker</b>\n\n"
        "Local calculator only. Actual coupon eligibility and fees must be confirmed in the official Swiggy app.\n\n"
        "Step 1/5: Enter cart total in ₹ (e.g. 599.50). Send /cancel to stop.",
        parse_mode=ParseMode.HTML,
    )

async def instamart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await instamart_start(update, context)

async def instamart_input(update: Update, context: ContextTypes.DEFAULT_TYPE, txt: str, stage: str):
    msg = update.effective_message
    if txt.strip().lower() == "/cancel":
        context.user_data["awaiting"] = None
        context.user_data.pop("instamart_values", None)
        await msg.reply_text("✅ Instamart calculation cancelled.")
        return
    values = context.user_data.setdefault("instamart_values", {})
    if stage in ("instamart_cart", "instamart_minimum", "instamart_maximum"):
        try:
            amount = float(txt.replace(",", "").replace("₹", "").strip())
            if not math.isfinite(amount) or amount < 0:
                raise ValueError
            amount = round(amount, 2)
        except (ValueError, OverflowError):
            await msg.reply_text("Enter a valid non-negative amount, e.g. 599 or 599.50.")
            return
        if stage == "instamart_cart":
            values["cart_total"] = amount
            context.user_data["awaiting"] = "instamart_minimum"
            await msg.reply_text("Step 2/5: Minimum order amount in ₹?")
            return
        if stage == "instamart_minimum":
            values["minimum_order"] = amount
            context.user_data["awaiting"] = "instamart_maximum"
            await msg.reply_text("Step 3/5: Maximum discount shown by the actual offer in ₹?")
            return
        values["maximum_discount"] = amount
        context.user_data["awaiting"] = "instamart_coupon"
        await msg.reply_text("Step 4/5: Enter coupon code shown in your app, or type skip.")
        return
    if stage == "instamart_coupon":
        values["coupon_code"] = "" if txt.strip().lower() == "skip" else txt.strip()[:100]
        context.user_data["awaiting"] = "instamart_eligible"
        await msg.reply_text("Step 5/5: Does the official app show the offer as eligible? Reply yes or no.")
        return
    if stage != "instamart_eligible":
        return
    answer = txt.strip().lower()
    if answer not in ("yes", "y", "no", "n"):
        await msg.reply_text("Reply yes or no, please.")
        return
    cart = values["cart_total"]
    minimum = values["minimum_order"]
    cap = values["maximum_discount"]
    errors = []
    if cart <= 0:
        errors.append("Cart total must be greater than zero.")
    if cart < minimum:
        errors.append(f"Cart must be at least ₹{minimum:.2f}.")
    if answer not in ("yes", "y"):
        errors.append("The official app does not show this offer as eligible.")
    discount = min(TARGET_DISCOUNT, cap, cart) if not errors else 0.0
    result = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "application": "Instamart Offer Debugger",
        "version": "1.0.0-telegram",
        "user_id": update.effective_user.id,
        "coupon_code_entered": values.get("coupon_code") or None,
        "cart_total": round(cart, 2),
        "minimum_order": round(minimum, 2),
        "requested_discount": TARGET_DISCOUNT,
        "maximum_discount": round(cap, 2),
        "calculated_discount": round(discount, 2),
        "calculated_payable": round(cart - discount, 2),
        "eligible_in_local_test": not errors,
        "validation_errors": errors,
        "verification_note": "Local calculation only. Confirm the actual discount, fees and payable total in the official Swiggy app."
    }
    try:
        existing = []
        if REPORT_FILE.exists():
            old = json.loads(REPORT_FILE.read_text(encoding="utf-8"))
            existing = old if isinstance(old, list) else [old]
        existing.append(result)
        REPORT_FILE.write_text(json.dumps(existing[-100:], indent=2, ensure_ascii=False), encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        log.exception("Could not save Instamart report")
    context.user_data["awaiting"] = None
    context.user_data.pop("instamart_values", None)
    errors_text = "\n".join("• " + escape(e) for e in errors) if errors else "• Local inputs pass validation."
    await msg.reply_text(
        "🛒 <b>Instamart calculation report</b>\n\n"
        f"Cart total: ₹{cart:.2f}\nMinimum order: ₹{minimum:.2f}\n"
        f"Requested discount: ₹{TARGET_DISCOUNT:.2f}\nMaximum discount: ₹{cap:.2f}\n"
        f"<b>Calculated discount: ₹{discount:.2f}</b>\n"
        f"<b>Calculated payable: ₹{cart-discount:.2f}</b>\n\n"
        f"{'✅ Local rules pass' if not errors else '⚠️ Local validation failed'}\n{errors_text}\n\n"
        f"ℹ️ {escape(result['verification_note'])}",
        parse_mode=ParseMode.HTML,
    )
