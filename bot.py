# ============================================================
# BHUSHAN SCIENCE BOT - v3.3 (New-Bot Identity Safe)
# ============================================================

import os, sqlite3, logging, asyncio, random, threading, traceback, time, re, base64, json
from html import escape
from urllib.request import Request, urlopen
from datetime import datetime, timedelta, date, time as dtime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import Conflict, InvalidToken
from flask import Flask
import pytz
from instamart_offer import instamart_start, instamart_input, instamart_command

# ================== CONFIG ==================
BOT_TOKEN = (os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or "").strip().strip('"').strip("'")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
DB_FILE = "bhushan_science.db"
TIMEZONE = "Asia/Kolkata"
# Public HTTPS URL of the Telegram Mini App. Set this in Render after hosting webapp/.
WEBAPP_URL = os.environ.get("WEBAPP_URL", "").strip()
MEME_CHAT_ID = os.environ.get("MEME_CHAT_ID", "").strip()
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "").strip()
# Optional safety check: set EXPECTED_BOT_USERNAME to the new BotFather username
# (without @). Startup fails if the configured token belongs to another bot.
EXPECTED_BOT_USERNAME = os.environ.get("EXPECTED_BOT_USERNAME", "").strip().lstrip("@").lower()
STICKER_URL = os.environ.get("STICKER_URL", "https://media.githubusercontent.com/media/ilyhalight/telegram-emoji-effects/master/webp/U+1F389/0.webp").strip()
ANIMATION_URL = os.environ.get("ANIMATION_URL", "https://i.imgur.com/LyHic3i.gif").strip()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)
IST = pytz.timezone(TIMEZONE)

# ================== FLASK WEB SERVER ==================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bhushan Science Bot is alive!"

@web_app.route('/health')
def health():
    return "OK"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    log.info(f"🌐 Starting Flask on port {port}")
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ================== TECHNIQUES ==================
TECHNIQUES = {
    "pomodoro": {"name": "🍅 Pomodoro", "work": 25, "break": 5, "cycles": 4, "desc": "25 min padho, 5 min break."},
    "deep_work": {"name": "🧠 Deep Work", "work": 50, "break": 10, "cycles": 2, "desc": "50 min deep focus."},
    "time_block": {"name": "⏰ Time Blocking", "work": 90, "break": 15, "cycles": 1, "desc": "90 min ek subject."},
    "active_recall": {"name": "🔁 Active Recall", "work": 30, "break": 5, "cycles": 2, "desc": "Padho, phir yaad karo."},
    "feynman": {"name": "🧑‍🏫 Feynman", "work": 40, "break": 10, "cycles": 1, "desc": "Simple bhasha me samjhao."},
    "spaced": {"name": "📅 Spaced Repetition", "work": 20, "break": 5, "cycles": 3, "desc": "Repeat se yaad rakho."},
    "interleaving": {"name": "🔀 Interleaving", "work": 60, "break": 10, "cycles": 1, "desc": "Multiple subjects mix."},
    "sq3r": {"name": "📖 SQ3R", "work": 45, "break": 10, "cycles": 1, "desc": "Survey, Question, Read..."},
    "mindmap": {"name": "🗺️ Mind Map", "work": 35, "break": 5, "cycles": 2, "desc": "Concept ka diagram."},
    "fifty_two": {"name": "⌛ 52/17 Rule", "work": 52, "break": 17, "cycles": 2, "desc": "Top performers ka rule."},
}

# ================== MODES ==================
MODES = {
    "serious": {"name": "🎯 Serious", "start": "✅ Study session started. Please maintain focused, professional study.", "break_msg": "⏸️ <b>Break Time</b> — hydrate, reset and return on time.", "nag": ["⚠️ Session is still active. Please complete the study task.", "⏰ Please return to your study session.", "📚 Consistency matters. Complete the scheduled work."], "reward": "🎉 Excellent work.", "punish": "❌ Session incomplete."},
    "fun": {"name": "😄 Fun", "start": "🚀 Chalo, books kholo aur brain ko warm-up do!", "break_msg": "☕ <b>Break!</b> Thoda relax, phir wapas grind.", "nag": ["😂 Oye scholar, comeback!", "👀 Focus kidhar gaya?", "🎈 Chalo bhai, session complete karo!"], "reward": "🥳 Nice! Brain ne attendance laga di.", "punish": "🙃 Session chhod diya? Brain ne tumhe seen kar diya."},
    "laparwah": {"name": "😈 Laparwah", "start": "😈 Abe chal, bahane band. Padhai shuru.", "break_msg": "😏 <b>Break.</b> Zyada hawa mein mat udna.", "nag": ["😤 Abe baklol, session chal raha hai!", "🤨 Kahan gayab ho gaya, chomu?", "😡 Oye nalayak, timer dekh!", "🙄 Padhne aaye the ya attendance lagane?", "💀 Last warning, bhaagoda!"], "reward": "🔥 Wah be! Aaj dimaag ne kaam kiya.", "punish": "🤡 Session adhura chhod diya. Ab 7 points ka fine lagega."},
}

SMART_JOKES = [
    "🧠 Smart joke: Nurse ne BP machine se kaha — “Tumhara pressure mujhe bhi pressure de raha hai!” 😄",
    "🧠 Smart joke: Anatomy student ka favourite map? — “Body ka internal Google Maps.” 😂",
    "🧠 Smart joke: Pharmacology student ne kaha — “Meri coffee ki dose PRN hai: jab tak jagta rahun.” ☕😄",
    "🧠 Smart joke: Physiology ne poocha, “Heart ka kaam?” Student bola — “Beat drop karna.” ❤️😂",
]

ROAST_LINES = [
    "😈 Abe topper, dimaag attendance pe tha kya?", "🤡 Baklol mode activated — timer ko ignore kar diya!",
    "😤 Oye chomu, padhne aaye the ya hawa khane?", "🙄 Nalayak scholar, kitab tumhe miss kar rahi hai.",
    "😂 Timer chal raha tha aur tum gayab — wah talent!", "😡 Abe bhaagode, session complete karna tha!",
    "🤨 Dimaag bola padh, tumne bola kal se. Classic.", "💀 Bhai, consistency ko block kyun kar diya?",
    "😈 Oye genius, excuse-making mein distinction mil jayega.", "🤡 Session chhod ke topper banoge? Wah confidence!",
    "😤 Abe susti ke brand ambassador, wapas aa.", "🙄 Notes khule reh gaye, student offline ho gaya.",
    "😂 Tumhara focus aur Wi‑Fi signal — dono unstable.", "😡 Oye chomu, timer se hide nahi kar sakte.",
    "💀 Padhai se itni dushmani kis baat ki?", "😈 Nalayak, reward ke 5 points ka sapna dekh rahe the na?",
    "🤨 Session complete karna tha, disappearance act nahi.", "🤡 Aaj ka medal: ‘Best at avoiding study’.",
    "😤 Abe scholar, excuses ka syllabus khatam kar.", "😂 Brain: study. You: later. Brain: seriously?",
    "🙄 Kitab tumhari taraf dekh ke soch rahi hai — ye kaun hai?", "😈 Oye baklol, comeback kar.",
    "💀 Timer ne tumhe hara diya. Shame, scholar.", "🤡 Padhai ko ghost karke topper nahi bante.",
    "😤 Last roast: ab kal se nahi, abhi se padh!",
]

async def send_style_media(context, uid, mode):
    try:
        if mode in ("fun", "laparwah") and STICKER_URL:
            await context.bot.send_sticker(uid, STICKER_URL)
    except Exception:
        pass
    try:
        if mode in ("fun", "laparwah") and ANIMATION_URL:
            await context.bot.send_animation(uid, ANIMATION_URL, caption="🎬 Focus mode ON!")
    except Exception:
        pass

# ================== BADGES ==================
BADGES = {
    "first_session": {"name": "🥇 First Session", "desc": "Pehli padhai"},
    "week_warrior": {"name": "🔥 Week Warrior", "desc": "7 din streak"},
    "month_master": {"name": "💪 Month Master", "desc": "30 din streak"},
    "point_hunter": {"name": "💎 Point Hunter", "desc": "500 points"},
    "legend": {"name": "👑 Legend", "desc": "2000 points"},
    "quiz_master": {"name": "🎯 Quiz Master", "desc": "10 quiz sahi"},
    "doubter": {"name": "❓ Curious Mind", "desc": "Pehla doubt"},
    "centurion": {"name": "⚡ Centurion", "desc": "100 sessions"},
    "technique_master": {"name": "🎓 Technique Master", "desc": "Saari techniques"},
}

# ================== DATABASE ==================
def init_db():
    c = sqlite3.connect(DB_FILE); cur = c.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, name TEXT, age INTEGER, user_class TEXT, stream TEXT, exam_target TEXT, points INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, last_study DATE, total_minutes INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0, verified INTEGER DEFAULT 0, current_session INTEGER DEFAULT 0, quiz_correct INTEGER DEFAULT 0, sessions_done INTEGER DEFAULT 0, mode TEXT DEFAULT 'serious', techniques_used TEXT DEFAULT '', joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY, added_by INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS channels(id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT UNIQUE, channel_name TEXT, channel_link TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, topic TEXT, question TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT, correct_option TEXT, explanation TEXT, difficulty TEXT, class_level TEXT, source TEXT DEFAULT 'ADMIN', exam TEXT, year INTEGER, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, subject TEXT, technique TEXT, mode TEXT, planned_minutes INTEGER, actual_minutes INTEGER DEFAULT 0, start_time TIMESTAMP, end_time TIMESTAMP, status TEXT DEFAULT 'running', q_asked INTEGER DEFAULT 0, q_correct INTEGER DEFAULT 0, photo_file_id TEXT, remaining_seconds INTEGER DEFAULT 0, paused_at TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS doubts(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, subject TEXT, question_text TEXT, photo_file_id TEXT, answer TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS points_log(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, points INTEGER, reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS quotes(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, author TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS memes(id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT, caption TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS badges(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, badge_key TEXT, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, badge_key))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS exam_dates(user_id INTEGER PRIMARY KEY, exam_name TEXT, exam_date DATE, set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS daily_quiz(id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_date DATE UNIQUE, question TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT, correct_option TEXT, explanation TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS quiz_answers(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, quiz_date DATE, chosen TEXT, correct INTEGER, UNIQUE(user_id, quiz_date))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS support_tickets(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, query TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', admin_id INTEGER, reply_text TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS admin_audit(id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER NOT NULL, action TEXT NOT NULL, details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS force_channels(id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL, username TEXT, invite_link TEXT, is_active INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    defaults = {'force_join_enabled': '0', 'force_join_configured': '0', 'join_fun_name': '', 'join_fun_link': '', 'reward_points': '10', 'punishment_points': '20', 'nag_message_count': '5', 'daily_points_target': '50', 'bot_name': 'Bhushan Science', 'welcome_msg': 'Padhai karo!', 'quote_time': '07:00', 'meme_time': '21:00', 'quiz_time': '20:00', 'break_reminder': '1', 'auto_meme_enabled': '1', 'meme_chat_id': MEME_CHAT_ID, 'auto_meme_interval': '1800'}
    for k, v in defaults.items(): cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    for _sql in ["ALTER TABLE users ADD COLUMN last_active TIMESTAMP","ALTER TABLE questions ADD COLUMN source TEXT DEFAULT 'ADMIN'","ALTER TABLE questions ADD COLUMN exam TEXT","ALTER TABLE questions ADD COLUMN year INTEGER","ALTER TABLE sessions ADD COLUMN remaining_seconds INTEGER DEFAULT 0","ALTER TABLE sessions ADD COLUMN paused_at TIMESTAMP"]:
        try: cur.execute(_sql)
        except sqlite3.OperationalError: pass
    cur.execute("INSERT OR IGNORE INTO admins(user_id,added_by) VALUES(?,?)", (OWNER_ID, OWNER_ID))
    for q, a in [("Padhai karne wale ke paas waqt nahi hota, aur na padhne wale ke paas bahane.", "Bhushan Science"), ("Success ka shortcut sirf mehnat aur consistency hai.", "Bhushan Science"), ("Jo aaj padhega, wahi kal topper banega.", "Bhushan Science")]:
        cur.execute("INSERT INTO quotes(text,author) SELECT ?,? WHERE NOT EXISTS(SELECT 1 FROM quotes)", (q, a))
    c.commit(); c.close()

def touch_user(uid):
    try:
        c = sqlite3.connect(DB_FILE)
        c.execute("UPDATE users SET last_active=CURRENT_TIMESTAMP WHERE user_id=?", (uid,))
        c.commit(); c.close()
    except Exception:
        pass

def db(): c = sqlite3.connect(DB_FILE); c.row_factory = sqlite3.Row; return c
def get_setting(k, d=None): c = db(); r = c.execute("SELECT value FROM settings WHERE key=?", (k,)).fetchone(); c.close(); return r['value'] if r else d
def set_setting(k, v): c = db(); c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, str(v))); c.commit(); c.close()
def is_admin(uid): c = db(); r = c.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,)).fetchone(); c.close(); return bool(r) or uid == OWNER_ID

def audit_admin(uid, action, details=''):
    try:
        c = db(); c.execute('INSERT INTO admin_audit(admin_id,action,details) VALUES(?,?,?)', (int(uid), str(action)[:120], str(details)[:1000])); c.commit(); c.close()
    except Exception:
        log.exception('Admin audit write failed')

def throttled(uid, context, interval=0.7):
    now = time.monotonic()
    last = context.bot_data.setdefault('_throttle_last', {})
    prev = last.get(int(uid), 0.0)
    if now - prev < interval:
        return True
    last[int(uid)] = now
    if len(last) > 10000:
        cutoff = now - 60
        context.bot_data['_throttle_last'] = {k:v for k,v in last.items() if v >= cutoff}
    return False

async def force_join_check(bot, uid):
    c = db(); channels = c.execute('SELECT * FROM force_channels WHERE is_active=1 ORDER BY id').fetchall(); c.close()
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch['channel_id'], user_id=uid)
            if member.status in ('left', 'kicked'):
                url = ch['invite_link'] or (f"https://t.me/{ch['username'].lstrip('@')}" if ch['username'] else '')
                if url: missing.append((ch['title'], url))
        except Exception as exc:
            # A bot removed from a channel must not crash or permanently block users.
            log.warning('Force-join check skipped for channel %s: %s', ch['channel_id'], exc)
            continue
    return missing

async def force_join_prompt(update, context, missing):
    buttons = [[InlineKeyboardButton('📢 Join ' + title[:40], url=url)] for title, url in missing]
    buttons.append([InlineKeyboardButton('✅ I Joined — Verify', callback_data='force_verify')])
    await update.effective_message.reply_text('🔒 <b>Channel join required</b>\n\nPehle active channel(s) join karo, phir verify dabao.', parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

async def force_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    missing=await force_join_check(context.bot, q.from_user.id)
    if missing:
        await q.answer('Abhi kuch channel join nahi hua.', show_alert=True)
        return
    await q.answer('Verified!')
    await q.edit_message_text('✅ Membership verified. Ab menu se continue karo.')

async def forceadd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if not is_admin(uid): return
    try:
        parts=[x.strip() for x in update.message.text.split(' ',1)[1].split('|')]
        if len(parts)!=4: raise ValueError('4 fields required')
        channel_id,title,username,invite_link=parts
        if not channel_id or not title or (username and not username.startswith('@')) or (invite_link and not invite_link.startswith('https://')): raise ValueError('invalid channel fields')
        c=db(); c.execute('INSERT INTO force_channels(channel_id,title,username,invite_link,is_active) VALUES(?,?,?,?,1) ON CONFLICT(channel_id) DO UPDATE SET title=excluded.title, username=excluded.username, invite_link=excluded.invite_link, is_active=1', (channel_id,title[:100],username[:100],invite_link[:500])); c.commit(); c.close()
        audit_admin(uid,'force_channel_add',channel_id)
        await update.message.reply_text('✅ Force-join channel add/update ho gaya. Bot ko us channel ka admin/member access dena zaroori hai.')
    except Exception as exc:
        await update.message.reply_text('Format: /forceadd CHANNEL_ID | title | @username_or_blank | invite_link_or_blank\nExample: /forceadd -1001234567890 | Study Channel | @studychannel | https://t.me/studychannel')
        log.exception('forceadd failed: %s',exc)

async def forcedisable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if not is_admin(uid): return
    try:
        channel_id=int(context.args[0])
        c=db(); c.execute('UPDATE force_channels SET is_active=0 WHERE id=?', (channel_id,)); changed=c.total_changes; c.commit(); c.close()
        audit_admin(uid,'force_channel_disable',f'id={channel_id}')
        await update.message.reply_text('✅ Channel disabled.' if changed else 'Channel ID nahi mila.')
    except Exception:
        await update.message.reply_text('Usage: /forcedisable ID (ID Force Join panel mein dikhega)')
def get_user(uid): c = db(); r = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone(); c.close(); return dict(r) if r else None
def create_user(uid, name): c = db(); c.execute("INSERT OR IGNORE INTO users(user_id,name) VALUES(?,?)", (uid, name)); c.commit(); c.close()
def update_user(uid, **kw):
    if not kw: return
    c = db(); f = ", ".join([f"{k}=?" for k in kw]); c.execute(f"UPDATE users SET {f} WHERE user_id=?", list(kw.values()) + [uid]); c.commit(); c.close()
def add_points(uid, pts, reason):
    c = db(); c.execute("UPDATE users SET points = MAX(0, points + ?) WHERE user_id=?", (pts, uid)); c.execute("INSERT INTO points_log(user_id,points,reason) VALUES(?,?,?)", (uid, pts, reason)); c.commit(); c.close(); check_badges(uid)
def all_channels(): c = db(); rows = c.execute("SELECT * FROM channels").fetchall(); c.close(); return [dict(r) for r in rows]
def has_badge(uid, key): c = db(); r = c.execute("SELECT 1 FROM badges WHERE user_id=? AND badge_key=?", (uid, key)).fetchone(); c.close(); return bool(r)
def give_badge(uid, key):
    if has_badge(uid, key): return False
    c = db(); c.execute("INSERT OR IGNORE INTO badges(user_id,badge_key) VALUES(?,?)", (uid, key)); c.commit(); c.close(); return True
def check_badges(uid):
    u = get_user(uid)
    if not u: return
    if u['sessions_done'] >= 1: give_badge(uid, 'first_session')
    if u['streak'] >= 7: give_badge(uid, 'week_warrior')
    if u['streak'] >= 30: give_badge(uid, 'month_master')
    if u['points'] >= 500: give_badge(uid, 'point_hunter')
    if u['points'] >= 2000: give_badge(uid, 'legend')
    if u['sessions_done'] >= 100: give_badge(uid, 'centurion')
    if u['quiz_correct'] >= 10: give_badge(uid, 'quiz_master')
    used = [x for x in (u.get('techniques_used') or '').split(',') if x]
    if len(set(used)) >= len(TECHNIQUES): give_badge(uid, 'technique_master')
def get_user_mode(uid):
    u = get_user(uid)
    mode = (u.get('mode') if u else None) or 'serious'
    # Normalize legacy/invalid database values so old users never crash
    # a study session because MODES[mode] does not exist.
    if mode not in MODES:
        mode = 'serious'
        if u:
            update_user(uid, mode=mode)
    return mode

# ================== ACCESS / FORCE-JOIN ==================
# Force-join is permanently disabled in the production bot.
# Keep this guard for compatibility with any old internal call sites, but it
# MUST NEVER send channel-join prompts or expose legacy channel data.
async def check_joined(context, user_id):
    return True

async def force_join_message(update, context):
    log.warning("⚠️ Legacy force_join_message() called; redirecting to normal /start flow")
    if getattr(update, "message", None):
        await start(update, context)

# ================== KEYBOARDS ==================
def class_selection_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 General Science", callback_data="cls_Other")]
    ])

def subject_selection_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Physics", callback_data="sub_Physics"), InlineKeyboardButton("Chemistry", callback_data="sub_Chemistry")],
        [InlineKeyboardButton("Biology", callback_data="sub_Biology"), InlineKeyboardButton("Maths", callback_data="sub_Maths")],
        [InlineKeyboardButton("English", callback_data="sub_English"), InlineKeyboardButton("GK", callback_data="sub_GK")],
        [InlineKeyboardButton("Other", callback_data="sub_Other")]
    ])

def technique_selection_kb():
    keys = list(TECHNIQUES.keys()); btns = []; row = []
    for k in keys:
        row.append(InlineKeyboardButton(TECHNIQUES[k]['name'], callback_data=f"tech_{k}"))
        if len(row) == 2: btns.append(row); row = []
    if row: btns.append(row)
    return InlineKeyboardMarkup(btns)

def main_menu_kb():
    app_button = KeyboardButton("📱 Study App", web_app=WebAppInfo(url=WEBAPP_URL)) if WEBAPP_URL else KeyboardButton("📱 Study App")
    return ReplyKeyboardMarkup([
        [app_button, KeyboardButton("📚 Padhai Shuru"), KeyboardButton("📸 Doubt Clear")],
        [KeyboardButton("🎉 Join Fun"), KeyboardButton("🎯 Exam Countdown"), KeyboardButton("📅 Aaj ka Target")],
        [KeyboardButton("🏆 Points"), KeyboardButton("🏅 Leaderboard"), KeyboardButton("🎖️ Badges")],
        [KeyboardButton("🎭 Mode Badlo"), KeyboardButton("📊 Report")],
        [KeyboardButton("🛒 Instamart Offer Checker")],
        [KeyboardButton("💭 Thought"), KeyboardButton("😂 Meme"), KeyboardButton("❓ Help")]
    ], resize_keyboard=True)

async def join_fun_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = get_setting('join_fun_name', '').strip()
    link = get_setting('join_fun_link', '').strip()
    if not link:
        await update.message.reply_text("🎉 <b>Join Fun</b>\n\nAbhi channel admin ne set nahi kiya hai.", parse_mode=ParseMode.HTML)
        return
    await update.message.reply_text(
        f"🎉 <b>Join Fun</b>\n\n📢 <b>{escape(name or 'Our Channel')}</b>\n\nCommunity se connected raho 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🚀 Join {name or 'Channel'}", url=link)]])
    )

def admin_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users", callback_data="a_users"), InlineKeyboardButton("📢 Channels", callback_data="a_channels")],
        [InlineKeyboardButton("🎉 Join Fun", callback_data="a_joinfun"), InlineKeyboardButton("⚙️ Settings", callback_data="a_settings")],
        [InlineKeyboardButton("❓ Questions", callback_data="a_questions")],
        [InlineKeyboardButton("💭 Quotes", callback_data="a_quotes"), InlineKeyboardButton("😂 Memes", callback_data="a_memes")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="a_broadcast"), InlineKeyboardButton("💬 Doubts", callback_data="a_doubts")],
        [InlineKeyboardButton("🎯 Daily Quiz", callback_data="a_dq"), InlineKeyboardButton("⏰ Times", callback_data="a_times")],
        [InlineKeyboardButton("🆘 Support Tickets", callback_data="a_support"), InlineKeyboardButton("📣 Force Join", callback_data="a_forcejoin")],
        [InlineKeyboardButton("📊 Stats", callback_data="a_stats"), InlineKeyboardButton("👤 Admins", callback_data="a_admins")],
        [InlineKeyboardButton("🛡️ Ban/Unban", callback_data="a_ban"), InlineKeyboardButton("🎁 Gift Points", callback_data="a_gift")],
    ])

# ================== MINI APP ==================
def app_launch_kb():
    if not WEBAPP_URL:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Mini App URL missing", callback_data="a_app_missing")]])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Open Bhushan Science App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("📚 Continue in Bot", callback_data="a_app_bot")],
    ])

async def app_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WEBAPP_URL:
        await update.message.reply_text(
            "⚠️ Mini App abhi configured nahi hai.\n\n"
            "Admin ko Render environment me WEBAPP_URL set karna hoga.",
            parse_mode=ParseMode.HTML,
        )
        return
    await update.message.reply_text(
        "🚀 <b>Bhushan Science App</b>\n\n"
        "🧠 Smart learning • 📝 Practice • 🤖 AI Doubt • 🏆 Progress\n\n"
        "👇 Telegram ke andar app kholo!",
        parse_mode=ParseMode.HTML,
        reply_markup=app_launch_kb(),
    )

async def app_missing_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer("Mini App URL configure nahi hua.", show_alert=True)

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # IMPORTANT: /start must never be blocked by legacy force-join/channel settings.
    # Older database rows/settings are ignored; onboarding starts immediately.
    uid = update.effective_user.id
    name = update.effective_user.first_name or "Student"
    touch_user(uid)
    create_user(uid, name)
    user = get_user(uid) or {}
    update_user(uid, verified=1)

    # Reset stale onboarding state from older bot versions so /start is
    # deterministic even after a redeploy.
    context.user_data['awaiting'] = None
    context.user_data['onboarding'] = True
    context.user_data['onboarding_step'] = 'mode'

    log.info("🚀 /start accepted: user=%s legacy_force_join_bypassed=1", uid)

    joke = random.choice(SMART_JOKES)
    await update.message.reply_text(
        f"👋 Namaste <b>{escape(name)}</b>!\n\n"
        f"🚀 <b>{escape(get_setting('bot_name', 'Bhushan Science Bot'))}</b> <b>LIVE</b> 🟢\n\n"
        f"{joke}\n\n"
        "🧭 <b>Onboarding:</b> Mode → General Science → Subject → Technique + Timer\n\n"
        "🎭 <b>Step 1 — Mode chuno:</b>\n"
        "Serious = professional • Fun = frank • Laparwah = savage/badtameez",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{'✅ ' if user.get('mode','serious') == 'serious' else ''}{MODES['serious']['name']}", callback_data="setm_serious")],
            [InlineKeyboardButton(f"{'✅ ' if user.get('mode','serious') == 'laparwah' else ''}{MODES['laparwah']['name']}", callback_data="setm_laparwah")],
            [InlineKeyboardButton(f"{'✅ ' if user.get('mode','serious') == 'fun' else ''}{MODES['fun']['name']}", callback_data="setm_fun")]
        ])
    )

async def verify_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if await check_joined(context, q.from_user.id): await q.edit_message_text("✅ Verified! Ab /start dabao.")
    else: await q.edit_message_text("❌ Saare channels join karo.")

async def class_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    touch_user(q.from_user.id)
    update_user(q.from_user.id, user_class="Other")
    context.user_data["onboarding_step"] = "subject"
    await q.edit_message_text(
        "📚 <b>General Science</b>\n\n📖 Subject chuno:",
        parse_mode=ParseMode.HTML,
        reply_markup=subject_selection_kb()
    )


# ================== MODE ==================
async def mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = get_user_mode(update.effective_user.id); btns = []
    for k, m in MODES.items(): btns.append([InlineKeyboardButton(f"{'✅ ' if k == cur else ''}{m['name']}", callback_data=f"setm_{k}")])
    await update.message.reply_text("🎭 <b>Apna Mode Chuno</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))

async def set_mode_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mode = q.data.replace("setm_", "")
    if mode not in MODES:
        mode = 'serious'
    update_user(q.from_user.id, mode=mode)
    context.user_data['onboarding'] = True
    context.user_data['onboarding_step'] = 'class'
    await q.edit_message_text(
        f"✅ Mode: <b>{MODES[mode]['name']}</b>\n\n"
        "🏫 <b>Step 2/4 — Class / Exam chuno:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=class_selection_kb()
    )

# ================== PADHAI ==================
def random_quote():
    """Return a fresh DB quote every time; never cache the previous quote."""
    try:
        c = db()
        r = c.execute("SELECT text, author FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone()
        c.close()
        if r:
            return f"💭 <b>Thought</b>\n\n<i>{escape(r['text'])}</i>\n\n— {escape(r['author'] or 'Bhushan Science')}"
    except Exception:
        pass
    return "💭 <b>Thought</b>\n\n<i>Consistency beats motivation. Aaj ka session aaj hi complete karo.</i>\n\n— Bhushan Science"

async def padhai_shuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    touch_user(uid)
    user = get_user(uid) or {}
    # "Padhai Shuru" is a complete fresh onboarding flow, same as /start.
    # Reset stale choices so the user gets Course/Class -> Term -> Subject ->
    # Topic -> Technique -> Timer every time instead of jumping to an old subject.
    context.user_data.clear()
    context.user_data['onboarding'] = True
    context.user_data['onboarding_step'] = 'mode'

    name = update.effective_user.first_name or "Student"
    mode = user.get('mode', 'serious')
    if mode not in MODES:
        mode = 'serious'
    quote = random_quote()
    joke = random.choice(SMART_JOKES)

    await update.message.reply_text(
        f"👋 <b>{escape(name)}</b>, chalo padhai shuru karte hain! 📚\n\n"
        f"{quote}\n\n"
        f"{joke}\n\n"
        "🧭 <b>Study Flow:</b> Mode → Course/Class → Semester/Year → Subject → Topic → Technique + Timer\n\n"
        "🎭 <b>Step 1 — Mode chuno:</b>\n"
        "Serious = professional • Fun = frank • Laparwah = savage/badtameez",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{'✅ ' if mode == 'serious' else ''}{MODES['serious']['name']}", callback_data="setm_serious")],
            [InlineKeyboardButton(f"{'✅ ' if mode == 'laparwah' else ''}{MODES['laparwah']['name']}", callback_data="setm_laparwah")],
            [InlineKeyboardButton(f"{'✅ ' if mode == 'fun' else ''}{MODES['fun']['name']}", callback_data="setm_fun")]
        ])
    )

async def technique_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id)
    tech = q.data.replace("tech_", "")
    if tech not in TECHNIQUES:
        await q.answer("Technique unavailable.", show_alert=True); return
    context.user_data['technique'] = tech
    context.user_data['onboarding'] = False
    context.user_data['onboarding_step'] = None
    subject = context.user_data.get('subject')
    if not subject:
        await q.edit_message_text("📚 Pehle subject choose karo.", reply_markup=subject_selection_kb()); return
    t = TECHNIQUES[tech]
    context.user_data['duration'] = t['work']
    await q.edit_message_text(f"🎭 <b>{t['name']}</b>\n\n{t['desc']}\n\n📚 Subject: <b>{escape(subject)}</b>\n⏱ Timer: <b>{t['work']} min</b>\n\n🚀 Timer STARTED!", parse_mode=ParseMode.HTML)
    await send_style_media(context, q.from_user.id, get_user_mode(q.from_user.id))
    await start_study_session(context, q.from_user.id)

async def session_pause_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    try: sid=int(q.data.replace("sess_pause_",""))
    except: return
    u=get_user(uid)
    if not u or u.get('current_session')!=sid: await q.answer("Session active nahi hai.",show_alert=True); return
    c=db(); row=c.execute("SELECT * FROM sessions WHERE id=? AND user_id=? AND status='running'",(sid,uid)).fetchone()
    if not row: c.close(); await q.answer("Already paused/stopped.",show_alert=True); return
    try: started=datetime.fromisoformat(str(row['start_time']))
    except: started=datetime.now()
    elapsed=max(0,int((datetime.now()-started).total_seconds()))
    remaining=max(1,int(row['remaining_seconds'] or row['planned_minutes']*60)-elapsed)
    c.execute("UPDATE sessions SET status='paused',remaining_seconds=?,paused_at=? WHERE id=?",(remaining,datetime.now(),sid)); c.commit(); c.close()
    await cancel_session_jobs(context.application,sid)
    await q.edit_message_text(f"⏸ <b>Timer PAUSED</b>\n\nSession #{sid}\n⏳ Remaining: <b>{remaining//60}m {remaining%60}s</b>",parse_mode=ParseMode.HTML,reply_markup=session_control_kb(sid,True))

async def session_resume_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    try: sid=int(q.data.replace("sess_resume_",""))
    except: return
    c=db(); row=c.execute("SELECT * FROM sessions WHERE id=? AND user_id=? AND status='paused'",(sid,uid)).fetchone()
    if not row: c.close(); await q.answer("Paused session nahi mila.",show_alert=True); return
    remaining=max(1,int(row['remaining_seconds'] or 1))
    c.execute("UPDATE sessions SET status='running',start_time=?,paused_at=NULL WHERE id=?",(datetime.now(),sid)); c.commit(); c.close()
    update_user(uid,current_session=sid)
    await schedule_session_jobs(context,uid,sid,remaining)
    await q.edit_message_text(f"▶️ <b>Timer RESUMED</b>\n\nSession #{sid}\n⏳ Remaining: <b>{remaining//60}m {remaining%60}s</b>",parse_mode=ParseMode.HTML,reply_markup=session_control_kb(sid))

async def session_stop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id
    try: sid=int(q.data.replace("sess_stop_",""))
    except: return
    u=get_user(uid)
    if not u or u.get('current_session')!=sid: await q.answer("Session active nahi hai.",show_alert=True); return
    await cancel_session_jobs(context.application,sid)
    now=datetime.now()
    c=db(); c.execute("UPDATE sessions SET status='failed',end_time=?,actual_minutes=CAST((julianday(?) - julianday(start_time))*1440 AS INTEGER) WHERE id=?",(now,now,sid)); c.commit(); c.close()
    update_user(uid,current_session=0); add_points(uid,-7,f"Session #{sid} ended early")
    await q.edit_message_text("⏹ <b>Session ended early.</b>\n\n💎 <b>-7 points</b>\nNext session me comeback karo.",parse_mode=ParseMode.HTML,reply_markup=main_menu_kb())

async def subject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); sub = q.data.replace("sub_", "")
    context.user_data['subject'] = sub
    if context.user_data.get('onboarding'):
        await q.edit_message_text(
            f"📚 <b>Subject: {escape(sub)}</b>\n\n🎭 <b>Step 4/4 — Technique choose karo:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=technique_selection_kb()
        )
        return
    default = TECHNIQUES[context.user_data.get('technique', 'pomodoro')]['work'] * TECHNIQUES[context.user_data.get('technique', 'pomodoro')]['cycles']
    await q.edit_message_text(
        f"Subject: <b>{escape(sub)}</b>\n\nKitni der?",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Default ({default}m)", callback_data=f"dur_{default}"), InlineKeyboardButton("30 min", callback_data="dur_30")],
            [InlineKeyboardButton("1 ghanta", callback_data="dur_60"), InlineKeyboardButton("2 ghante", callback_data="dur_120")],
            [InlineKeyboardButton("3 ghante", callback_data="dur_180"), InlineKeyboardButton("Custom", callback_data="dur_custom")]
        ])
    )

async def duration_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id); dur = q.data.replace("dur_", "")
    if dur == "custom":
        context.user_data['awaiting'] = 'custom_minutes'
        await q.edit_message_text("Kitne minute? Number bhejo:")
        return
    context.user_data['duration'] = int(dur)
    context.user_data['awaiting'] = None
    await q.edit_message_text(f"⏱ <b>{dur} min</b>\n\n📚 Session start ho raha hai — photo ki zarurat nahi hai.", parse_mode=ParseMode.HTML)
    await start_study_session(context, q.from_user.id)

async def custom_minutes_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting') != 'custom_minutes': return
    touch_user(update.effective_user.id)
    try:
        dur = int(update.message.text.strip())
        if dur < 5 or dur > 1440: raise ValueError
    except:
        await update.message.reply_text("❌ 5-1440 ke beech number:")
        return
    context.user_data['duration'] = dur
    context.user_data['awaiting'] = None
    await update.message.reply_text(f"⏱ <b>{dur} min</b>\n\n📚 Session start ho raha hai — photo ki zarurat nahi hai.", parse_mode=ParseMode.HTML)
    await start_study_session(context, update.effective_user.id)

async def cancel_session_jobs(app, sid):
    jq = app.job_queue
    if not jq:
        return
    for name in (f"session_break_{sid}", f"session_reminder_{sid}", f"session_nag_{sid}", f"session_quiz_timeout_{sid}"):
        for job in jq.get_jobs_by_name(name):
            job.schedule_removal()

async def schedule_session_jobs(context, uid, sid, remaining_seconds):
    jq=context.job_queue
    if not jq: return
    for name in (f"session_break_{sid}",f"session_reminder_{sid}",f"session_nag_{sid}"):
        for job in jq.get_jobs_by_name(name): job.schedule_removal()
    remaining_seconds=max(1,int(remaining_seconds))
    jq.run_once(session_reminder,remaining_seconds,chat_id=uid,data={'sid':sid},name=f"session_reminder_{sid}")
    jq.run_once(nag_check,remaining_seconds+300,chat_id=uid,data={'sid':sid},name=f"session_nag_{sid}")

async def start_study_session(context, uid):
    sub=context.user_data.get('subject','General'); dur=int(context.user_data.get('duration',30))
    tech=context.user_data.get('technique','pomodoro'); mode=get_user_mode(uid)
    c=db(); active=c.execute("SELECT id FROM sessions WHERE user_id=? AND status IN ('running','paused')",(uid,)).fetchone()
    if active:
        c.close(); await context.bot.send_message(uid,"⚠️ Tumhara ek study session already active hai. Pehle usko complete/end karo."); return
    cur=c.execute("INSERT INTO sessions(user_id,subject,technique,mode,planned_minutes,start_time,photo_file_id,status,remaining_seconds) VALUES(?,?,?,?,?,?,?,?,?)",(uid,sub,tech,mode,dur,datetime.now(),None,'running',dur*60))
    sid=cur.lastrowid; c.commit(); c.close()
    update_user(uid,current_session=sid); touch_user(uid)
    u=get_user(uid); used=[x for x in (u.get('techniques_used') or '').split(',') if x]
    if tech not in used: used.append(tech)
    update_user(uid,techniques_used=','.join(used)); check_badges(uid)
    context.user_data['session_id']=sid; context.user_data['awaiting']=None
    t=TECHNIQUES[tech]
    if context.job_queue:
        for cyc in range(t['cycles']):
            delay=t['work']*(cyc+1)+t['break']*cyc
            if delay < dur:
                context.job_queue.run_once(break_msg_job,delay*60,chat_id=uid,data={'sid':sid,'cycle':cyc+1,'mode':mode},name=f"session_break_{sid}")
        await schedule_session_jobs(context,uid,sid,dur*60)
    await context.bot.send_message(uid,f"✅ <b>Session #{sid}</b>\n\n{t['name']} | {escape(sub)} | {dur} min\n\n{MODES[mode]['start']}\n\n📌 Timer controls neeche milenge.",parse_mode=ParseMode.HTML,reply_markup=session_control_kb(sid))
    await context.bot.send_message(uid,"📚 Focus mode ON — study session start ho gaya.",reply_markup=main_menu_kb())

async def study_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting') != 'study_photo': return
    if not update.message.photo: await update.message.reply_text("❌ Photo bhejo."); return
    uid = update.effective_user.id; photo = update.message.photo[-1].file_id
    sub = context.user_data.get('subject', 'General'); dur = context.user_data.get('duration', 30)
    tech = context.user_data.get('technique', 'pomodoro'); mode = get_user_mode(uid)
    c = db()
    cur = c.execute("INSERT INTO sessions(user_id,subject,technique,mode,planned_minutes,start_time,photo_file_id,status) VALUES(?,?,?,?,?,?,?,?)", (uid, sub, tech, mode, dur, datetime.now(), photo, 'running'))
    sid = cur.lastrowid; c.commit(); c.close()
    update_user(uid, current_session=sid)
    u = get_user(uid); used = [x for x in (u.get('techniques_used') or '').split(',') if x]
    if tech not in used: used.append(tech)
    update_user(uid, techniques_used=','.join(used)); check_badges(uid)
    context.user_data['session_id'] = sid; context.user_data['awaiting'] = None
    t = TECHNIQUES[tech]
    for cyc in range(t['cycles']):
        delay_min = t['work'] * (cyc + 1) + t['break'] * cyc
        if delay_min < dur: context.job_queue.run_once(break_msg_job, delay_min * 60, chat_id=uid, data={'sid': sid, 'cycle': cyc + 1, 'mode': mode})
    context.job_queue.run_once(session_reminder, dur * 60, chat_id=uid, data={'sid': sid})
    context.job_queue.run_once(nag_check, (dur + 5) * 60, chat_id=uid, data={'sid': sid})
    await update.message.reply_text(f"✅ <b>Session #{sid}</b>\n\n{t['name']} | {sub} | {dur} min\n\n{MODES[mode]['start']}", parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())

async def break_msg_job(context: ContextTypes.DEFAULT_TYPE):
    sid = context.job.data['sid']; uid = context.job.chat_id; u = get_user(uid)
    if not u or u.get('current_session') != sid: context.job.schedule_removal(); return
    await context.bot.send_message(uid, f"{MODES[context.job.data.get('mode', 'serious')]['break_msg']}\n\n🔁 Cycle {context.job.data['cycle']} complete!", parse_mode=ParseMode.HTML)

async def session_reminder(context: ContextTypes.DEFAULT_TYPE):
    sid = context.job.data['sid']; uid = context.job.chat_id; u = get_user(uid)
    if not u or u.get('current_session') != sid: return
    c=db(); c.execute("UPDATE sessions SET status='awaiting_quiz' WHERE id=? AND status='running'",(sid,)); c.commit(); c.close()
    await ask_questions(context, uid, sid)

async def nag_check(context: ContextTypes.DEFAULT_TYPE):
    sid = context.job.data['sid']; uid = context.job.chat_id; u = get_user(uid)
    if not u or u.get('current_session') != sid: return
    c=db(); sr=c.execute("SELECT status FROM sessions WHERE id=?",(sid,)).fetchone(); c.close()
    if sr and sr['status'] == 'awaiting_quiz': return
    mode = get_user_mode(uid)
    if mode == "laparwah":
        lines = ROAST_LINES
    elif mode == "fun":
        lines = MODES["fun"]["nag"]
    else:
        lines = MODES["serious"]["nag"]
    for i in range(1, 26):
        if get_user(uid).get('current_session') != sid: return
        line = lines[(i - 1) % len(lines)]
        try:
            await context.bot.send_message(uid, f"{line}\n\n<code>Reminder {i}/25</code>", parse_mode=ParseMode.HTML)
        except Exception: pass
        await asyncio.sleep(0.6 if i % 5 else 1)
    if get_user(uid).get('current_session') != sid: return
    add_points(uid, -7, f"Session #{sid} incomplete")
    c = db(); c.execute("UPDATE sessions SET status='failed', end_time=? WHERE id=?", (datetime.now(), sid)); c.commit(); c.close()
    update_user(uid, current_session=0)
    await context.bot.send_message(uid, f"{MODES[mode]['punish']}\n\n💎 <b>-7 points</b>", parse_mode=ParseMode.HTML)
    await send_style_media(context, uid, mode)

# ================== QUESTIONS ==================
async def ask_questions(context, uid, sid):
    u = get_user(uid)
    cls = (u or {}).get('user_class', 'Other')
    c = db()
    rows = c.execute(
        "SELECT * FROM questions WHERE class_level IN (?, 'All') AND upper(COALESCE(source,''))='PYQ' ORDER BY RANDOM() LIMIT 3",
        (cls,),
    ).fetchall()
    c.close()
    if not rows:
        await context.bot.send_message(uid, "ℹ️ Timer complete. Is class ke verified PYQs abhi available nahi hain. Session complete mark kiya ja raha hai.")
        await finish_session(context, uid, sid, 0, 0)
        return
    context.user_data[f'qq_{sid}'] = [dict(r) for r in rows]
    context.user_data[f'qi_{sid}'] = 0
    context.user_data[f'qc_{sid}'] = 0
    # Prevent sessions getting stuck forever when a student leaves the quiz unanswered.
    if context.job_queue:
        for job in context.job_queue.get_jobs_by_name(f"session_quiz_timeout_{sid}"):
            job.schedule_removal()
        context.job_queue.run_once(
            quiz_timeout,
            15 * 60,
            chat_id=uid,
            data={'sid': sid},
            name=f"session_quiz_timeout_{sid}",
        )
    await context.bot.send_message(uid, f"📝 Session #{sid} time up!\n\nAb {len(rows)} questions (15 min ke andar answer karo):")
    await send_next_question(context, uid, sid)

async def send_next_question(context, uid, sid):
    qs = context.user_data.get(f'qq_{sid}', []); i = context.user_data.get(f'qi_{sid}', 0)
    if i >= len(qs): await finish_session(context, uid, sid, len(qs), context.user_data.get(f'qc_{sid}', 0)); return
    q = qs[i]
    btns = [
        [InlineKeyboardButton(f"{opt.upper()}) {escape(str(q[f'option_{opt}']))}", callback_data=f"ans_{sid}_{i}_{opt}")]
        for opt in ['a', 'b', 'c', 'd'] if q.get(f'option_{opt}')
    ]
    question_text = escape(str(q.get('question') or 'Question unavailable'))
    await context.bot.send_message(
        uid,
        f"<b>Q{i+1}.</b> {question_text}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(btns),
    )

async def answer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    try:
        _, raw_sid, raw_index, chosen = q.data.split("_", 3)
        sid = int(raw_sid)
        question_index = int(raw_index)
    except (ValueError, TypeError):
        await q.answer("Question data invalid hai.", show_alert=True)
        return
    user = get_user(uid)
    if not user or int(user.get('current_session') or 0) != sid:
        await q.answer("Ye quiz ab active nahi hai.", show_alert=True)
        return
    c = db()
    session = c.execute("SELECT status FROM sessions WHERE id=? AND user_id=?", (sid, uid)).fetchone()
    c.close()
    if not session or session['status'] != 'awaiting_quiz':
        await q.answer("Ye quiz ab active nahi hai.", show_alert=True)
        return
    qs = context.user_data.get(f'qq_{sid}', [])
    i = context.user_data.get(f'qi_{sid}', 0)
    if i >= len(qs) or question_index != i:
        await q.answer("Is question ka answer already process ho chuka hai.", show_alert=True)
        return
    await q.answer()
    correct = str(qs[i].get('correct_option', 'a')).strip().lower()
    expl = escape(str(qs[i].get('explanation') or ''))
    if chosen == correct:
        context.user_data[f'qc_{sid}'] = context.user_data.get(f'qc_{sid}', 0) + 1
        await q.edit_message_text(f"✅ Sahi!\n{expl}", parse_mode=ParseMode.HTML)
    else:
        await q.edit_message_text(f"❌ Galat. Sahi: <b>{escape(correct.upper())}</b>\n{expl}", parse_mode=ParseMode.HTML)
    context.user_data[f'qi_{sid}'] = i + 1
    await asyncio.sleep(0.5)
    await send_next_question(context, uid, sid)

async def quiz_timeout(context: ContextTypes.DEFAULT_TYPE):
    sid = int(context.job.data['sid'])
    uid = int(context.job.chat_id)
    user = get_user(uid)
    if not user or int(user.get('current_session') or 0) != sid:
        return
    c = db()
    cur = c.execute(
        "UPDATE sessions SET status='failed', end_time=? WHERE id=? AND user_id=? AND status='awaiting_quiz'",
        (datetime.now(), sid, uid),
    )
    c.commit()
    changed = cur.rowcount
    c.close()
    if changed != 1:
        return
    add_points(uid, -7, f"Session #{sid} quiz not completed")
    update_user(uid, current_session=0)
    for key in (f'qq_{sid}', f'qi_{sid}', f'qc_{sid}'):
        context.user_data.pop(key, None)
    await context.bot.send_message(
        uid,
        "⏰ Quiz ka time khatam ho gaya aur answers complete nahi hue. Session incomplete mark hua.\n\n💎 -7 points. Agla session jab ready ho tab shuru karna.",
        reply_markup=main_menu_kb(),
    )


async def finish_session(context, uid, sid, asked, correct):
    # Complete atomically so duplicate/stale callbacks cannot award points twice.
    c = db()
    cur = c.execute(
        "UPDATE sessions SET status='completed', end_time=?, q_asked=?, q_correct=? "
        "WHERE id=? AND user_id=? AND status='awaiting_quiz'",
        (datetime.now(), asked, correct, sid, uid),
    )
    if cur.rowcount != 1:
        c.close()
        return
    row = c.execute("SELECT planned_minutes FROM sessions WHERE id=? AND user_id=?", (sid, uid)).fetchone()
    planned = row['planned_minutes'] if row else 0
    c.commit()
    c.close()
    await cancel_session_jobs(context.application, sid)
    for key in (f'qq_{sid}', f'qi_{sid}', f'qc_{sid}'):
        context.user_data.pop(key, None)
    u = get_user(uid); total_min = (u['total_minutes'] or 0) + planned
    today = date.today().isoformat(); last = u.get('last_study'); streak = u.get('streak') or 0
    if last == today: pass
    elif last == (date.today() - timedelta(days=1)).isoformat(): streak += 1
    else: streak = 1
    update_user(uid, total_minutes=total_min, streak=streak, last_study=today, current_session=0, sessions_done=(u['sessions_done'] or 0) + 1)
    add_points(uid, total_pts, f"Session #{sid} complete")
    await context.bot.send_message(uid, f"{MODES[get_user_mode(uid)]['reward']}\n\n✅ Sahi: {correct}/{asked}\n💎 <b>+5 reward points</b>\n🔥 Streak: {streak} din\n⏱ Total: {total_min} min", parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
    await send_style_media(context, uid, get_user_mode(uid))

# ================== AI DOUBT SCANNER ==================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini").strip()

async def ai_doubt_answer(image_bytes=None, question_text=""):
    if not OPENAI_API_KEY: return None
    prompt = """You are Bhushan Science Bot, a clear and accurate general science study tutor.
Read the student's question/image carefully and answer in clear Hinglish/English. Explain concepts step by step, define important terms, and use simple examples where helpful.
For health-related science questions, provide general educational information only; do not diagnose a real person or prescribe treatment. For urgent symptoms, advise seeking help from a qualified healthcare professional.
For other subjects, answer directly at an appropriate student level. If an image is blurry or unreadable, say so instead of inventing text."""
    content=[{"type":"text","text":prompt}]
    if question_text and question_text != "[Photo]": content.append({"type":"text","text":"Student question: "+question_text})
    if image_bytes:
        b64=base64.b64encode(image_bytes).decode("ascii")
        content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b64,"detail":"high"}})
    payload={"model":OPENAI_VISION_MODEL,"messages":[{"role":"system","content":"Accurate general science tutor. Never fabricate unreadable information."},{"role":"user","content":content}],"temperature":0.2,"max_tokens":3000}
    def call():
        req=Request("https://api.openai.com/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+OPENAI_API_KEY,"Content-Type":"application/json"},method="POST")
        with urlopen(req,timeout=90) as resp: return json.loads(resp.read().decode())
    try:
        data=await asyncio.to_thread(call)
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log.exception("AI doubt scan failed: %s", e); return None

async def ai_doubt_from_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not OPENAI_API_KEY:
        await update.message.reply_text("⚠️ AI scanner configured nahi hai. Render Environment me OPENAI_API_KEY set karo.")
        return
    photo=update.message.photo[-1]
    caption=(update.message.caption or "").strip()
    await update.message.reply_text("🔎 Photo scan ho rahi hai...\n🧠 AI answer prepare kar raha hai.")
    try:
        tg_file=await context.bot.get_file(photo.file_id)
        image_bytes=bytes(await tg_file.download_as_bytearray())
        answer=await ai_doubt_answer(image_bytes, caption or "[Photo]")
        await update.message.reply_text("🤖 AI Answer\n\n"+answer[:4000] if answer else "⚠️ Answer generate nahi ho paya. Clear photo bhejo.")
    except Exception as e:
        log.exception("Photo doubt processing failed: %s", e)
        await update.message.reply_text("⚠️ Photo scan me problem hui. Clear image bhejo ya doubt text me likho.")

# ================== DOUBT ==================
async def doubt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'doubt_photo'
    await update.message.reply_text("📸 <b>Doubt Clear</b>\n\nPhoto bhejo ya text likho.", parse_mode=ParseMode.HTML)

async def doubt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting') != 'doubt_photo': return
    uid = update.effective_user.id
    if update.message.photo:
        fid = update.message.photo[-1].file_id; txt = update.message.caption or "[Photo]"
        context.user_data['awaiting'] = None
        if give_badge(uid, 'doubter'): await context.bot.send_message(uid, "🎉 Badge: ❓ Curious Mind!")
        await ai_doubt_from_photo(update, context)
        return
    fid = None; txt = update.message.text
    answer = search_answer(txt)
    if not answer and OPENAI_API_KEY: answer = await ai_doubt_answer(None, txt)
    c = db(); c.execute("INSERT INTO doubts(user_id,question_text,photo_file_id,answer,status) VALUES(?,?,?,?,?)", (uid, txt, fid, answer, 'answered' if answer else 'pending')); c.commit(); c.close()
    context.user_data['awaiting'] = None
    if give_badge(uid, 'doubter'): await context.bot.send_message(uid, "🎉 Badge: ❓ Curious Mind!")
    if answer: await update.message.reply_text(f"🤖 <b>Answer:</b>\n{answer}", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("📩 Doubt admin ko bhej diya.")
        c = db(); admins = [r['user_id'] for r in c.execute("SELECT user_id FROM admins").fetchall()]; c.close()
        for a in admins:
            try:
                if fid: await context.bot.send_photo(a, fid, caption=f"❓ Doubt from {uid}:\n{txt}")
                else: await context.bot.send_message(a, f"❓ Doubt from {uid}:\n{txt}")
            except: pass

def search_answer(query):
    if not query or len(query) < 3: return None
    c = db(); rows = c.execute("SELECT question, correct_option, option_a, option_b, option_c, option_d, explanation FROM questions").fetchall(); c.close()
    ql = query.lower()
    for r in rows:
        if any(w in r['question'].lower() for w in ql.split() if len(w) > 4):
            opts = {'a': r['option_a'], 'b': r['option_b'], 'c': r['option_c'], 'd': r['option_d']}
            return f"<b>{r['question']}</b>\n\n✅ Sahi: {r['correct_option'].upper()}) {opts[r['correct_option'].lower()]}\n\n📖 {r['explanation'] or ''}"
    return None

# ================== REPORT / POINTS / HELP ==================
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; u = get_user(uid)
    if not u: await update.message.reply_text("Pehle /start karo."); return
    c = db(); done = c.execute("SELECT COUNT(*) c FROM sessions WHERE user_id=? AND status='completed'", (uid,)).fetchone()['c']; c.close()
    c = db(); ed = c.execute("SELECT * FROM exam_dates WHERE user_id=?", (uid,)).fetchone(); c.close()
    exam_line = ""
    if ed:
        try: days = (datetime.fromisoformat(ed['exam_date']).date() - date.today()).days; exam_line = f"\n🎯 {ed['exam_name']}: {days} din bache"
        except: pass
    await update.message.reply_text(f"📊 <b>Meri Report</b>\n\n👤 {u['name']}\n🏫 Class: {u['user_class']}\n🎭 Mode: {MODES.get(u.get('mode', 'serious'), MODES['serious'])['name']}\n💎 Points: {u['points']}\n🔥 Streak: {u['streak']} din\n⏱ Total: {u['total_minutes']} min\n✅ Sessions: {done}{exam_line}", parse_mode=ParseMode.HTML)

async def points_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; c = db(); rows = c.execute("SELECT points, reason FROM points_log WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,)).fetchall(); c.close()
    if not rows: await update.message.reply_text("Koi history nahi."); return
    txt = "🏆 <b>Recent Points</b>\n\n"
    for r in rows: txt += f"{'➕' if r['points'] > 0 else '➖'} {abs(r['points'])} — {r['reason']}\n"
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

async def today_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; target = int(get_setting('daily_points_target', '50'))
    c = db(); r = c.execute("SELECT COALESCE(SUM(points),0) s FROM points_log WHERE user_id=? AND date(created_at)=date('now') AND points>0", (uid,)).fetchone(); c.close()
    tp = r['s'] or 0
    await update.message.reply_text(f"📅 <b>Aaj ka Target</b>\n\n🎯 Target: {target}\n📈 Aaj: {tp}\n{'✅ Complete!' if tp >= target else '⏳ Aur mehnat!'}", parse_mode=ParseMode.HTML)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ <b>Help & Support</b>\n\n📚 Padhai Shuru\n📸 Doubt Clear\n🎭 Mode Badlo\n🎯 Exam Countdown\n📊 Report\n🏆 Points\n🏅 Leaderboard\n🎖️ Badges\n💭 Thought / 😂 Meme\n\nAgar help chahiye, neeche button dabao ya /support likho.\nCommands: /start /admin /help /support /cancel /mode", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🆘 Contact Support", callback_data="support_new")]]))

async def support_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'support_query'
    await update.effective_message.reply_text('🆘 Apni problem ya question ek message mein bhejo. Cancel karne ke liye /cancel.')

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = None
    await update.effective_message.reply_text('✅ Current action cancel kar diya.')

async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if throttled(q.from_user.id, context):
        await q.answer('Thoda wait karo.', show_alert=False); return
    await q.answer()
    if q.data == 'support_new':
        context.user_data['awaiting'] = 'support_query'
        await q.message.reply_text('🆘 Apni problem ya question ek message mein bhejo. Cancel karne ke liye /cancel.')
        return
    if not is_admin(q.from_user.id):
        await q.answer('Admin only.', show_alert=True); return
    parts = q.data.split(':')
    if len(parts) != 2:
        return
    action, raw_id = parts
    try: ticket_id = int(raw_id)
    except ValueError: return
    c = db(); ticket = c.execute('SELECT * FROM support_tickets WHERE id=?', (ticket_id,)).fetchone(); c.close()
    if not ticket:
        await q.message.reply_text('Ticket nahi mila.'); return
    if action == 'ticket_reply':
        context.user_data['awaiting'] = 'support_reply'
        context.user_data['support_ticket_id'] = ticket_id
        await q.message.reply_text(f'✍️ Ticket #{ticket_id} ka reply bhejo. /cancel se cancel hoga.')
    elif action == 'ticket_close':
        c = db(); c.execute("UPDATE support_tickets SET status='closed', admin_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND status!='closed'", (q.from_user.id, ticket_id)); c.commit(); c.close()
        audit_admin(q.from_user.id, 'support_ticket_close', f'ticket_id={ticket_id}')
        await q.message.reply_text(f'✅ Ticket #{ticket_id} close kar diya.')

async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await mode_menu(update, context)

# ================== LEADERBOARD / BADGES ==================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = db(); rows = c.execute("""SELECT u.name, u.user_id, COALESCE(SUM(p.points),0) pts FROM users u LEFT JOIN points_log p ON u.user_id=p.user_id AND p.created_at >= datetime('now','-7 days') GROUP BY u.user_id ORDER BY pts DESC LIMIT 10""").fetchall(); c.close()
    txt = "🏅 <b>Weekly Leaderboard</b>\n\n"
    for i, r in enumerate(rows): txt += f"{['🥇','🥈','🥉'][i] if i < 3 else f'{i+1}.'} {r['name']} — <b>{r['pts']}</b> pts\n"
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

async def badges_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; c = db(); rows = c.execute("SELECT badge_key FROM badges WHERE user_id=?", (uid,)).fetchall(); c.close()
    have = {r['badge_key'] for r in rows}; txt = "🎖️ <b>Aapke Badges</b>\n\n"
    for k, b in BADGES.items(): txt += f"{'✅' if k in have else '🔒'} {b['name']} — {b['desc']}\n"
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

# ================== EXAM ==================
async def exam_countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'exam_name'
    await update.message.reply_text("🎯 Exam ka naam bhejo:", parse_mode=ParseMode.HTML)

async def exam_name_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting') != 'exam_name': return
    context.user_data['exam_name'] = update.message.text.strip()[:50]; context.user_data['awaiting'] = 'exam_date'
    await update.message.reply_text("📅 Date bhejo (YYYY-MM-DD):")

async def exam_date_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting') != 'exam_date': return
    try: d = datetime.fromisoformat(update.message.text.strip()).date()
    except: await update.message.reply_text("❌ Format: YYYY-MM-DD"); return
    uid = update.effective_user.id; name = context.user_data.get('exam_name', 'Exam')
    c = db(); c.execute("INSERT OR REPLACE INTO exam_dates(user_id,exam_name,exam_date) VALUES(?,?,?)", (uid, name, d.isoformat())); c.commit(); c.close()
    context.user_data['awaiting'] = None; days = (d - date.today()).days
    await update.message.reply_text(f"✅ <b>{name}</b>\n📅 {d.isoformat()}\n⏳ <b>{days} din bache</b>", parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())

# ================== THOUGHT / MEME ==================
async def thought_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random_quote(), parse_mode=ParseMode.HTML)

async def meme_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = db(); r = c.execute("SELECT file_id, caption FROM memes ORDER BY RANDOM() LIMIT 1").fetchone(); c.close()
    if not r: await update.message.reply_text("😂 Koi meme nahi."); return
    try: await context.bot.send_photo(update.effective_user.id, r['file_id'], caption=f"😂 {r['caption'] or ''}")
    except: pass

# ================== ADMIN ==================
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): await update.message.reply_text("❌ Not admin."); return
    await update.message.reply_text("🛠️ <b>Admin Panel</b>", parse_mode=ParseMode.HTML, reply_markup=admin_menu_kb())

async def admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if throttled(q.from_user.id, context):
        await q.answer('Thoda wait karo.', show_alert=False); return
    await q.answer()
    if not is_admin(q.from_user.id): await q.edit_message_text("❌ Not admin."); return
    d = q.data
    audit_admin(q.from_user.id, 'admin_callback', d)
    if d == "a_menu": await q.edit_message_text("🛠️ Admin Panel", reply_markup=admin_menu_kb()); return
    if d == 'a_support':
        c = db(); rows = c.execute("SELECT id,user_id,query,status,created_at FROM support_tickets WHERE status IN ('pending','replied') ORDER BY id DESC LIMIT 12").fetchall(); c.close()
        if not rows:
            await q.edit_message_text('🆘 Koi open support ticket nahi hai.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='a_menu')]])); return
        buttons=[]; lines=['🆘 <b>Support Tickets</b>']
        for t in rows:
            lines.append(f"\\n<b>#{t['id']}</b> • user <code>{t['user_id']}</code> • {escape(t['status'])}\\n{escape(t['query'][:180])}")
            buttons.append([InlineKeyboardButton(f"✍️ Reply #{t['id']}", callback_data=f"ticket_reply:{t['id']}"), InlineKeyboardButton(f"✅ Close #{t['id']}", callback_data=f"ticket_close:{t['id']}")])
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data='a_menu')])
        await q.edit_message_text('\\n'.join(lines), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons)); return
    if d == 'a_forcejoin':
        c = db(); rows = c.execute('SELECT id,title,channel_id,invite_link,is_active FROM force_channels ORDER BY id DESC').fetchall(); c.close()
        lines=['📣 <b>Force Join Channels</b>']
        for ch in rows: lines.append(f"\\n#{ch['id']} • {escape(ch['title'])} • {'🟢 active' if ch['is_active'] else '⚪ disabled'}\\n<code>{escape(ch['channel_id'])}</code>")
        lines.append('\\nAdd: /forceadd CHANNEL_ID | title | @username_or_blank | invite_link_or_blank\\nDisable: /forcedisable ID')
        await q.edit_message_text('\\n'.join(lines), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='a_menu')]])); return
    if d == "a_channels": await channels_panel(q, context); return
    if d == "a_joinfun":
        context.user_data['awaiting'] = 'join_fun'
        name = get_setting('join_fun_name', '').strip()
        link = get_setting('join_fun_link', '').strip()
        await q.edit_message_text(
            "🎉 <b>Join Fun Channel</b>\n\n"
            f"Current: <b>{escape(name or 'Not set')}</b>\n"
            f"Link: <code>{escape(link or 'Not set')}</code>\n\n"
            "Send: <code>Channel Name | https://t.me/yourchannel</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Clear", callback_data="a_joinfun_clear")],
                [InlineKeyboardButton("🔙 Back", callback_data="a_menu")]
            ])
        )
        return
    if d == "a_joinfun_clear":
        set_setting('join_fun_name', '')
        set_setting('join_fun_link', '')
        context.user_data['awaiting'] = None
        await q.edit_message_text("✅ Join Fun channel clear ho gaya.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]]))
        return
    if d == "a_settings": await settings_panel(q, context); return
    if d == "a_times": await times_panel(q, context); return
    if d == "a_quotes":
        c = db(); cnt = c.execute("SELECT COUNT(*) c FROM quotes").fetchone()['c']; c.close()
        await q.edit_message_text(f"💭 Quotes — {cnt}\n\n/addquote text | author\n/delquote id\n/listquotes", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_memes":
        c = db(); cnt = c.execute("SELECT COUNT(*) c FROM memes").fetchone()['c']; c.close()
        await q.edit_message_text(f"😂 Memes — {cnt}\n\n/addmeme (photo+caption)\n/delmeme id\n/listmemes", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_questions": await q.edit_message_text("❓ /addq Sub|Topic|Q|A|B|C|D|Correct|Expl|Class", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_stats":
        c = db(); users = c.execute("SELECT COUNT(*) c FROM users").fetchone()['c']; sessions = c.execute("SELECT COUNT(*) c FROM sessions").fetchone()['c']; done = c.execute("SELECT COUNT(*) c FROM sessions WHERE status='completed'").fetchone()['c']; c.close()
        await q.edit_message_text(f"📊 Users: {users}\nSessions: {sessions} ({done} done)", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_users": await q.edit_message_text("👥 /userinfo ID\n/ban ID\n/unban ID\n/gift ID points", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_admins":
        c = db(); rows = c.execute("SELECT user_id FROM admins").fetchall(); c.close()
        txt = "👤 <b>Admins</b>\n\n" + "\n".join([f"• <code>{r['user_id']}</code>" for r in rows]) + "\n\n/addadmin ID\n/removeadmin ID"
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_broadcast": context.user_data['awaiting'] = 'broadcast'; await q.edit_message_text("📣 Broadcast message bhejo:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="a_menu")]])); return
    if d == "a_ban": await q.edit_message_text("🛡️ /ban ID  |  /unban ID", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_gift": await q.edit_message_text("🎁 /gift ID points", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_doubts":
        c = db(); rows = c.execute("SELECT id,user_id,question_text FROM doubts WHERE status='pending' LIMIT 10").fetchall(); c.close()
        txt = "💬 Pending Doubts:\n\n"
        for r in rows: txt += f"#{r['id']} — {r['user_id']}: {r['question_text'][:50]}\n"
        txt += "\n/reply ID answer"
        await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]])); return
    if d == "a_dq": context.user_data['awaiting'] = 'daily_quiz'; await q.edit_message_text("🎯 Format: Q | A | B | C | D | correct | explanation", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="a_menu")]])); return

async def channels_panel(q, context):
    chs = all_channels(); txt = "📢 <b>Channels</b>\n\n"
    if chs:
        for ch in chs: txt += f"• {ch['channel_name']} — <code>{ch['channel_id']}</code>\n"
    else: txt += "Koi nahi.\n"
    txt += "\n/addchannel <id> | name | link\n/delchannel <id>"
    btns = [
        [InlineKeyboardButton("🚫 Force Join Disabled", callback_data="a_menu")],
        [InlineKeyboardButton("🔙 Back", callback_data="a_menu")]
    ]
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))

async def fj_toggle(update, context):
    q = update.callback_query; await q.answer()
    if q.data == "a_fjon":
        # Explicit admin action is the only way to activate force-join.
        set_setting('force_join_configured', '1')
        set_setting('force_join_enabled', '1')
    else:
        set_setting('force_join_enabled', '0')
        set_setting('force_join_configured', '0')
    await channels_panel(q, context)

async def settings_panel(q, context):
    keys = ['reward_points', 'punishment_points', 'nag_message_count', 'daily_points_target', 'bot_name', 'welcome_msg']
    txt = "⚙️ <b>Settings</b>\n\n"
    for k in keys: txt += f"<code>{k}</code> = {get_setting(k)}\n"
    txt += "\n/set key value"
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]]))

async def times_panel(q, context):
    txt = "⏰ <b>Auto Post Times (IST)</b>\n\n"
    for k in ['quote_time', 'meme_time', 'quiz_time']: txt += f"<code>{k}</code> = {get_setting(k)}\n"
    txt += "\n/settime quote_time 07:00"
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="a_menu")]]))

# ================== ADMIN COMMANDS ==================
async def addchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        args = update.message.text.split(" ", 1)[1].split("|"); cid, name, link = [a.strip() for a in args]
        c = db(); c.execute("INSERT OR REPLACE INTO channels(channel_id,channel_name,channel_link) VALUES(?,?,?)", (cid, name, link)); c.commit(); c.close()
        await update.message.reply_text(f"✅ {name}")
    except Exception as e: await update.message.reply_text(f"❌ /addchannel -100xxx | Name | link\n{e}")

async def delchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        cid = update.message.text.split(" ", 1)[1].strip()
        c = db(); c.execute("DELETE FROM channels WHERE channel_id=?", (cid,)); c.commit(); c.close()
        await update.message.reply_text("✅ Removed.")
    except: await update.message.reply_text("❌ /delchannel id")

async def addq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        a = update.message.text.split(" ", 1)[1].split("|"); sub, top, q, oa, ob, oc, od, cor, expl, cls = [x.strip() for x in a[:10]]
        c = db(); c.execute("""INSERT INTO questions(subject,topic,question,option_a,option_b,option_c,option_d,correct_option,explanation,class_level) VALUES(?,?,?,?,?,?,?,?,?,?)""", (sub, top, q, oa, ob, oc, od, cor.lower(), expl, cls)); c.commit(); c.close()
        await update.message.reply_text("✅ Question added!")
    except Exception as e: await update.message.reply_text(f"❌ Format error: {e}")

async def addpyq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        a=[x.strip() for x in update.message.text.split(" ",1)[1].split("|")]
        if len(a)<12: raise ValueError("12 fields required")
        sub,top,q,oa,ob,oc,od,cor,expl,cls,year_s,exam=a[:12]
        year=int(year_s)
        if cor.lower() not in ("a","b","c","d"): raise ValueError("Correct must be A/B/C/D")
        c=db(); c.execute("""INSERT INTO questions(subject,topic,question,option_a,option_b,option_c,option_d,correct_option,explanation,class_level,source,exam,year) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(sub,top,q,oa,ob,oc,od,cor.lower(),expl,cls,"PYQ",exam,year)); c.commit(); c.close()
        await update.message.reply_text(f"✅ Verified PYQ added — {exam} {year}")
    except Exception as e: await update.message.reply_text(f"❌ /addpyq Subject|Topic|Q|A|B|C|D|Correct|Explanation|Class|Year|Exam\n{e}")

async def addquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        a = update.message.text.split(" ", 1)[1].split("|"); text = a[0].strip(); author = a[1].strip() if len(a) > 1 else "Bhushan Science"
        c = db(); c.execute("INSERT INTO quotes(text,author) VALUES(?,?)", (text, author)); c.commit(); c.close()
        await update.message.reply_text("✅ Quote added!")
    except: await update.message.reply_text("❌ /addquote text | author")

async def delquote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        qid = int(update.message.text.split(" ", 1)[1]); c = db(); c.execute("DELETE FROM quotes WHERE id=?", (qid,)); c.commit(); c.close()
        await update.message.reply_text("✅ Removed.")
    except: await update.message.reply_text("❌ /delquote id")

async def listquotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    c = db(); rows = c.execute("SELECT id,text,author FROM quotes ORDER BY id DESC LIMIT 20").fetchall(); c.close()
    txt = "💭 <b>Quotes</b>\n\n"
    for r in rows: txt += f"<code>{r['id']}</code> — {r['text'][:60]}\n"
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

async def addmeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not update.message.photo: await update.message.reply_text("❌ Photo ke saath /addmeme bhejo."); return
    fid = update.message.photo[-1].file_id; cap = (update.message.caption or "").replace("/addmeme", "").strip()
    c = db(); c.execute("INSERT INTO memes(file_id,caption) VALUES(?,?)", (fid, cap)); c.commit(); c.close()
    await update.message.reply_text("✅ Meme added!")

async def delmeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        mid = int(update.message.text.split(" ", 1)[1]); c = db(); c.execute("DELETE FROM memes WHERE id=?", (mid,)); c.commit(); c.close()
        await update.message.reply_text("✅ Removed.")
    except: await update.message.reply_text("❌ /delmeme id")

async def listmemes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    c = db(); rows = c.execute("SELECT id,caption FROM memes ORDER BY id DESC LIMIT 20").fetchall(); c.close()
    txt = "😂 <b>Memes</b>\n\n"
    for r in rows: txt += f"<code>{r['id']}</code> — {(r['caption'] or '')[:50]}\n"
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML)

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        k, v = update.message.text.split(" ", 1)[1].split(" ", 1); set_setting(k.strip(), v.strip())
        await update.message.reply_text(f"✅ {k} = {v}")
    except: await update.message.reply_text("❌ /set key value")

async def settime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        parts = update.message.text.split(); k = parts[1]; t = parts[2]; datetime.strptime(t, "%H:%M")
        set_setting(k, t); reschedule_jobs(context.application)
        await update.message.reply_text(f"✅ {k} = {t}")
    except Exception as e: await update.message.reply_text(f"❌ /settime quote_time 07:00\n{e}")

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        uid = int(update.message.text.split(" ", 1)[1]); c = db(); c.execute("INSERT OR IGNORE INTO admins(user_id,added_by) VALUES(?,?)", (uid, OWNER_ID)); c.commit(); c.close()
        await update.message.reply_text(f"✅ Admin: {uid}")
    except: await update.message.reply_text("❌ /addadmin ID")

async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        uid = int(update.message.text.split(" ", 1)[1])
        if uid == OWNER_ID: await update.message.reply_text("Owner remove nahi."); return
        c = db(); c.execute("DELETE FROM admins WHERE user_id=?", (uid,)); c.commit(); c.close()
        await update.message.reply_text(f"✅ Removed: {uid}")
    except: await update.message.reply_text("❌ /removeadmin ID")

async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        uid = int(update.message.text.split(" ", 1)[1]); u = get_user(uid)
        if not u: await update.message.reply_text("Nahi mila."); return
        await update.message.reply_text(f"👤 <b>{u['name']}</b>\nID: <code>{uid}</code>\nClass: {u['user_class']}\nMode: {u['mode']}\nPoints: {u['points']}\nStreak: {u['streak']}\nMin: {u['total_minutes']}\nSessions: {u['sessions_done']}\nBanned: {u['is_banned']}", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("❌ /userinfo ID")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        uid = int(update.message.text.split(" ", 1)[1]); update_user(uid, is_banned=1)
        await update.message.reply_text(f"🚫 Banned: {uid}")
    except: await update.message.reply_text("❌ /ban ID")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        uid = int(update.message.text.split(" ", 1)[1]); update_user(uid, is_banned=0)
        await update.message.reply_text(f"✅ Unbanned: {uid}")
    except: await update.message.reply_text("❌ /unban ID")

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        parts = update.message.text.split(); uid, pts = int(parts[1]), int(parts[2]); add_points(uid, pts, "Admin gift")
        await update.message.reply_text(f"🎁 {pts} → {uid}")
        try: await context.bot.send_message(uid, f"🎁 Admin ne {pts} points diye!")
        except: pass
    except: await update.message.reply_text("❌ /gift ID points")

async def reply_doubt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    try:
        parts = update.message.text.split(" ", 2); did = int(parts[1]); ans = parts[2]
        c = db(); row = c.execute("SELECT user_id FROM doubts WHERE id=?", (did,)).fetchone()
        c.execute("UPDATE doubts SET answer=?, status='answered' WHERE id=?", (ans, did)); c.commit(); c.close()
        if row:
            try: await context.bot.send_message(row['user_id'], f"💬 Admin reply:\n{ans}")
            except: pass
        await update.message.reply_text("✅ Sent.")
    except: await update.message.reply_text("❌ /reply ID answer")

async def broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if context.user_data.get('awaiting') != 'broadcast': return
    context.user_data['awaiting'] = None
    c = db(); users = [r['user_id'] for r in c.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]; c.close()
    sent = 0
    for u in users:
        try:
            if update.message.photo: await context.bot.send_photo(u, update.message.photo[-1].file_id, caption=update.message.caption or "")
            else: await context.bot.send_message(u, update.message.text)
            sent += 1; await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ Sent {sent}/{len(users)}")

# ================== DAILY QUIZ ==================
async def daily_quiz_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if context.user_data.get('awaiting') != 'daily_quiz': return
    try:
        parts = [x.strip() for x in update.message.text.split("|")]; q, a, b, cc, d, cor, expl = parts[:7]
        today = date.today().isoformat(); c = db()
        c.execute("INSERT OR REPLACE INTO daily_quiz(quiz_date,question,option_a,option_b,option_c,option_d,correct_option,explanation) VALUES(?,?,?,?,?,?,?,?)", (today, q, a, b, cc, d, cor.lower(), expl))
        c.commit(); c.close(); context.user_data['awaiting'] = None
        await update.message.reply_text("✅ Aaj ka quiz set!")
        await broadcast_daily_quiz(context)
    except Exception as e: await update.message.reply_text(f"❌ Format: Q|A|B|C|D|correct|expl\n{e}")

async def broadcast_daily_quiz(context):
    today = date.today().isoformat(); c = db()
    q = c.execute("SELECT * FROM daily_quiz WHERE quiz_date=?", (today,)).fetchone()
    users = [r['user_id'] for r in c.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]; c.close()
    if not q: return
    text = f"🎯 <b>Daily Quiz</b>\n\n<b>{q['question']}</b>\n\nA) {q['option_a']}\nB) {q['option_b']}\nC) {q['option_c']}\nD) {q['option_d']}"
    btns = [[InlineKeyboardButton("A", callback_data="dq_a"), InlineKeyboardButton("B", callback_data="dq_b"), InlineKeyboardButton("C", callback_data="dq_c"), InlineKeyboardButton("D", callback_data="dq_d")]]
    for u in users:
        try:
            await context.bot.send_message(u, text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))
            await asyncio.sleep(0.05)
        except: pass

async def daily_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id; chosen = q.data.replace("dq_", "")
    today = date.today().isoformat(); c = db()
    dq = c.execute("SELECT * FROM daily_quiz WHERE quiz_date=?", (today,)).fetchone()
    if not dq: await q.answer("Aaj quiz nahi.", show_alert=True); c.close(); return
    ex = c.execute("SELECT 1 FROM quiz_answers WHERE user_id=? AND quiz_date=?", (uid, today)).fetchone()
    if ex: await q.answer("Already done.", show_alert=True); c.close(); return
    correct = 1 if chosen == dq['correct_option'] else 0
    c.execute("INSERT INTO quiz_answers(user_id,quiz_date,chosen,correct) VALUES(?,?,?,?)", (uid, today, chosen, correct)); c.commit(); c.close()
    if correct:
        add_points(uid, 15, "Daily Quiz correct")
        c = db(); cc = c.execute("SELECT COUNT(*) c FROM quiz_answers WHERE user_id=? AND correct=1", (uid,)).fetchone()['c']; c.close()
        update_user(uid, quiz_correct=cc)
        await q.edit_message_text(f"✅ Sahi! +15\n\n📖 {dq['explanation'] or ''}")
    else: await q.edit_message_text(f"❌ Galat. Sahi: <b>{dq['correct_option'].upper()}</b>\n\n📖 {dq['explanation'] or ''}", parse_mode=ParseMode.HTML)

async def idle_coach_job(context):
    c=db()
    rows=c.execute("""SELECT user_id FROM users WHERE is_banned=0 AND COALESCE(current_session,0)=0 AND (last_active IS NULL OR last_active <= datetime('now','-2 minutes')) ORDER BY user_id""").fetchall()
    c.close()
    if not rows: return
    c=db()
    quote=c.execute("SELECT text,author FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    meme=c.execute("SELECT caption FROM memes ORDER BY RANDOM() LIMIT 1").fetchone()
    c.close()
    qtxt=f"💭 {quote['text']}" if quote else "💭 Aaj ka rule: consistency > motivation."
    mtxt=f"😂 Meme: {meme['caption']}" if meme and meme['caption'] else "😂 Meme: Notes kholne ka notification aa gaya… ab ignore mat karna."
    msg=("⏰ <b>2-minute Study Check</b>\n\n📚 Abhi active study session nahi hai.\n"
         "👉 2 minute bhi revise kar lo — phir session start karo.\n\n"+qtxt+"\n"+mtxt+
         "\n\n🇮🇳 NORCET/INC content official-source curriculum ke according maintained hai.")
    for r in rows:
        try:
            await context.bot.send_message(r["user_id"],msg,parse_mode=ParseMode.HTML)
            touch_user(r["user_id"]); await asyncio.sleep(0.05)
        except Exception: pass

# ================== AUTO JOBS ==================
async def daily_quote_job(context):
    c = db(); q = c.execute("SELECT text,author FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone()
    users = [r['user_id'] for r in c.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]; c.close()
    if not q: return
    text = f"💭 <b>Good Morning</b>\n\n<i>{q['text']}</i>\n\n— {q['author']}"
    for u in users:
        try: await context.bot.send_message(u, text, parse_mode=ParseMode.HTML); await asyncio.sleep(0.05)
        except: pass

async def daily_meme_job(context):
    c = db(); m = c.execute("SELECT file_id,caption FROM memes ORDER BY RANDOM() LIMIT 1").fetchone()
    users = [r['user_id'] for r in c.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()]; c.close()
    if not m: return
    for u in users:
        try: await context.bot.send_photo(u, m['file_id'], caption=f"😂 {m['caption'] or ''}"); await asyncio.sleep(0.05)
        except: pass

async def auto_meme_job(context):
    if str(get_setting('auto_meme_enabled','1')).lower() not in ('1','true','yes','on'): return
    chat_id=get_setting('meme_chat_id',MEME_CHAT_ID).strip()
    if not chat_id: return
    c=db(); rows=c.execute("SELECT id,file_id,caption FROM memes ORDER BY id").fetchall(); c.close()
    last=int(get_setting('auto_meme_last_id','0') or 0)
    choices=[dict(r) for r in rows if r['id']!=last] or [dict(r) for r in rows]
    try:
        if choices:
            m=random.choice(choices)
            await context.bot.send_photo(chat_id,m['file_id'],caption=f"😂 {m.get('caption') or 'Bhushan Science Meme'}")
            set_setting('auto_meme_last_id',m['id'])
        else: await context.bot.send_message(chat_id,random.choice(SMART_JOKES+ROAST_LINES))
    except Exception as e: log.warning("Auto meme publish failed: %s",e)

async def daily_quiz_job(context): await broadcast_daily_quiz(context)

async def exam_countdown_daily(context):
    c = db(); rows = c.execute("SELECT user_id, exam_name, exam_date FROM exam_dates").fetchall(); c.close()
    for r in rows:
        try:
            days = (datetime.fromisoformat(r['exam_date']).date() - date.today()).days
            if days < 0: continue
            msg = f"🎯 <b>{r['exam_name']}</b>\n⏳ {days} din bache"
            try: await context.bot.send_message(r['user_id'], msg, parse_mode=ParseMode.HTML)
            except: pass
            await asyncio.sleep(0.05)
        except: pass

def reschedule_jobs(app):
    # python-telegram-bot only creates JobQueue when the [job-queue]
    # extra is installed. Keep startup safe even if a stale Render build
    # is ever deployed without that optional dependency.
    job_queue = app.job_queue
    if job_queue is None:
        log.error("❌ JobQueue unavailable. Install python-telegram-bot[job-queue].")
        return

    for name in ["daily_quote", "daily_meme", "daily_quiz", "exam_countdown", "idle_coach", "auto_meme_publish"]:
        for j in job_queue.get_jobs_by_name(name):
            j.schedule_removal()

    def pt(s):
        try: h, m = s.split(":"); return dtime(int(h), int(m), tzinfo=IST)
        except: return None
    qt = pt(get_setting('quote_time', '07:00')); mt = pt(get_setting('meme_time', '21:00')); zt = pt(get_setting('quiz_time', '20:00'))
    if qt: job_queue.run_daily(daily_quote_job, time=qt, name="daily_quote")
    if mt: job_queue.run_daily(daily_meme_job, time=mt, name="daily_meme")
    if zt: job_queue.run_daily(daily_quiz_job, time=zt, name="daily_quiz")
    job_queue.run_daily(
        exam_countdown_daily,
        time=dtime(8, 0, tzinfo=IST),
        name="exam_countdown",
    )
    job_queue.run_repeating(idle_coach_job, interval=120, first=120, name="idle_coach")
    try:
        meme_interval = max(300, int(get_setting("auto_meme_interval", "1800") or 1800))
    except (TypeError, ValueError):
        meme_interval = 1800
    job_queue.run_repeating(auto_meme_job, interval=meme_interval, first=60, name="auto_meme_publish")

    # Recover timers after Render restarts/redeploys. User context is in-memory,
    # so an interrupted quiz is safely re-opened rather than left stuck forever.
    c = db()
    active_rows = c.execute(
        "SELECT id, user_id, status, start_time, planned_minutes, remaining_seconds "
        "FROM sessions WHERE status IN ('running', 'awaiting_quiz') ORDER BY id"
    ).fetchall()
    for row in active_rows:
        sid, uid = int(row['id']), int(row['user_id'])
        if row['status'] == 'awaiting_quiz':
            c.execute(
                "UPDATE sessions SET status='running', remaining_seconds=1, start_time=? WHERE id=?",
                (datetime.now().isoformat(), sid),
            )
            remaining = 1
        else:
            try:
                started = datetime.fromisoformat(str(row['start_time']))
                elapsed = max(0, int((datetime.now() - started).total_seconds()))
            except (TypeError, ValueError):
                elapsed = 0
            remaining = max(1, int(row['remaining_seconds'] or int(row['planned_minutes'] or 1) * 60) - elapsed)
        c.commit()
        job_queue.run_once(
            session_reminder,
            remaining,
            chat_id=uid,
            data={'sid': sid},
            name=f"session_reminder_{sid}",
        )
        job_queue.run_once(
            nag_check,
            remaining + 300,
            chat_id=uid,
            data={'sid': sid},
            name=f"session_nag_{sid}",
        )
        log.info("Recovered active study session sid=%s user=%s remaining=%ss", sid, uid, remaining)
    c.close()

# ================== CHANNEL POST ==================
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if not post: return
    try: await context.bot.forward_message(OWNER_ID, post.chat_id, post.message_id)
    except: pass

# ================== ROUTER ==================
async def msg_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid = update.effective_user.id
    if throttled(uid, context):
        return
    log.info("📩 Incoming Telegram message: user=%s type=%s text=%r", uid, "photo" if update.message.photo else "text", (update.message.text or update.message.caption or "")[:120])
    touch_user(uid); u = get_user(uid)
    if u and u.get('is_banned'): await update.message.reply_text("🚫 Banned."); return
    txt = (update.message.text or "").strip(); aw = context.user_data.get('awaiting')
    # Do not block an in-progress support/admin flow, and keep help accessible.
    if aw not in ('support_query','support_reply','join_fun','broadcast','daily_quiz') and not (aw and aw.startswith('instamart_')) and txt not in ('❓ Help',):
        missing = await force_join_check(context.bot, uid)
        if missing:
            await force_join_prompt(update, context, missing)
            return
    if aw and aw.startswith('instamart_'):
        await instamart_input(update, context, txt, aw)
        return
    if txt == "🛒 Instamart Offer Checker":
        await instamart_start(update, context)
        return
    if aw == 'support_query':
        query_text = (update.message.text or update.message.caption or '').strip()
        if not query_text:
            await update.message.reply_text('Text message bhejo ya /cancel karo.'); return
        c = db(); cur = c.execute('INSERT INTO support_tickets(user_id,query,status) VALUES(?,?,\'pending\')', (uid, query_text[:4000])); ticket_id = cur.lastrowid; admins = [r['user_id'] for r in c.execute('SELECT user_id FROM admins').fetchall()]; c.commit(); c.close()
        context.user_data['awaiting'] = None
        await update.message.reply_text(f'✅ Support request #{ticket_id} submit ho gayi. Admin reply karega.')
        kb = InlineKeyboardMarkup([[InlineKeyboardButton('✍️ Reply', callback_data=f'ticket_reply:{ticket_id}'), InlineKeyboardButton('✅ Close', callback_data=f'ticket_close:{ticket_id}')]])
        for aid in set(admins + ([OWNER_ID] if OWNER_ID > 0 else [])):
            try: await context.bot.send_message(aid, f'🆘 <b>Support Ticket #{ticket_id}</b>\\nUser: <code>{uid}</code>\\n\\n{escape(query_text[:3500])}', parse_mode=ParseMode.HTML, reply_markup=kb)
            except Exception: log.exception('Failed to notify support admin %s for ticket %s', aid, ticket_id)
        return
    if aw == 'support_reply':
        if not is_admin(uid): context.user_data['awaiting']=None; return
        ticket_id = context.user_data.get('support_ticket_id')
        reply_text = (update.message.text or '').strip()
        if not reply_text: await update.message.reply_text('Text reply bhejo ya /cancel.'); return
        c = db(); ticket = c.execute('SELECT user_id,status FROM support_tickets WHERE id=?', (ticket_id,)).fetchone()
        if not ticket or ticket['status'] == 'closed':
            c.close(); context.user_data['awaiting']=None; await update.message.reply_text('Ticket missing ya closed hai.'); return
        c.execute("UPDATE support_tickets SET status='replied',admin_id=?,reply_text=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (uid, reply_text[:4000], ticket_id)); c.commit(); c.close()
        context.user_data['awaiting']=None; context.user_data.pop('support_ticket_id', None)
        audit_admin(uid, 'support_ticket_reply', f'ticket_id={ticket_id}')
        try: await context.bot.send_message(ticket['user_id'], f'💬 <b>Support reply — ticket #{ticket_id}</b>\\n\\n{escape(reply_text[:3900])}', parse_mode=ParseMode.HTML)
        except Exception: log.exception('Unable to deliver support reply for ticket %s', ticket_id)
        await update.message.reply_text(f'✅ Reply ticket #{ticket_id} par bhej diya.')
        return
    if aw == 'custom_minutes': await custom_minutes_msg(update, context); return
    if aw == 'doubt_photo': await doubt_photo(update, context); return
    if aw == 'broadcast': await broadcast_msg(update, context); return
    if aw == 'exam_name': await exam_name_msg(update, context); return
    if aw == 'exam_date': await exam_date_msg(update, context); return
    if aw == 'daily_quiz': await daily_quiz_admin_msg(update, context); return
    if aw == 'join_fun':
        if not is_admin(uid):
            context.user_data['awaiting'] = None
            return
        try:
            name, link = [x.strip() for x in txt.split("|", 1)]
            if not name or not link.startswith(("https://", "http://", "tg://")):
                raise ValueError
            set_setting('join_fun_name', name[:80])
            set_setting('join_fun_link', link[:500])
            context.user_data['awaiting'] = None
            await update.message.reply_text(f"✅ Join Fun updated!\n\n🎉 {escape(name)}\n🔗 {escape(link)}", parse_mode=ParseMode.HTML, reply_markup=admin_menu_kb())
        except Exception:
            await update.message.reply_text("❌ Format: <code>Channel Name | https://t.me/yourchannel</code>", parse_mode=ParseMode.HTML)
        return

    if txt == "📱 Study App": await app_cmd(update, context); return
    if txt == "📚 Padhai Shuru": await padhai_shuru(update, context); return
    if txt == "📸 Doubt Clear": await doubt_start(update, context); return
    if txt == "🎭 Mode Badlo": await mode_menu(update, context); return
    if txt == "🎉 Join Fun": await join_fun_view(update, context); return
    if txt in ("📊 Report", "📊 Meri Report"): await report(update, context); return
    if txt == "🏆 Points": await points_cmd(update, context); return
    if txt == "📅 Aaj ka Target": await today_target(update, context); return
    if txt == "🏅 Leaderboard": await leaderboard(update, context); return
    if txt == "🎖️ Badges": await badges_view(update, context); return
    if txt == "🎯 Exam Countdown": await exam_countdown(update, context); return
    if txt == "💭 Thought": await thought_view(update, context); return
    if txt == "😂 Meme": await meme_view(update, context); return
    if txt == "❓ Help": await help_cmd(update, context); return

    # Any other normal chat message goes to AI instead of being ignored.
    if txt:
        if not OPENAI_API_KEY:
            await update.message.reply_text("⚠️ AI chat configured nahi hai. Admin ko OPENAI_API_KEY set karna hoga.")
            return
        try:
            await context.bot.send_chat_action(chat_id=uid, action="typing")
            answer = await ai_doubt_answer(None, txt)
            if answer:
                await update.message.reply_text("🤖 " + answer[:4000])
            else:
                await update.message.reply_text("⚠️ AI se reply generate nahi ho paya. Thodi der baad dobara try karo.")
        except Exception as e:
            log.exception("AI chat reply failed: %s", e)
            await update.message.reply_text("⚠️ AI reply me temporary problem hui. Dobara try karo.")
        return

# ================== GLOBAL TELEGRAM ERROR HANDLER ==================
async def bot_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    try:
        err = context.error
        log.exception("❌ Telegram handler error: %s", err)
        if update and getattr(update, "effective_message", None):
            try:
                await update.effective_message.reply_text("⚠️ Bot me temporary error aaya. Please /start dobara try karo.")
            except Exception:
                pass
    except Exception:
        log.exception("❌ Error handler itself failed")


# ================== MAIN ==================
async def post_init(app):
    # Clear any stale Telegram webhook before polling. A previous webhook
    # configuration can otherwise prevent getUpdates from receiving messages.
    try:
        await app.bot.delete_webhook(drop_pending_updates=False)
        me = await app.bot.get_me()
        actual_username = (me.username or "").lower()
        log.info("🔗 Telegram connection ready: @%s (id=%s)", me.username, me.id)
        if EXPECTED_BOT_USERNAME and actual_username != EXPECTED_BOT_USERNAME:
            raise RuntimeError(
                f"BOT_TOKEN belongs to @{me.username}, but EXPECTED_BOT_USERNAME is @{EXPECTED_BOT_USERNAME}. "
                "Fix the Render environment variable BOT_TOKEN before continuing."
            )
    except InvalidToken:
        log.error("❌ TELEGRAM TOKEN INVALID/REVOKED — check BOT_TOKEN in hosting environment variables.")
        raise
    except Exception as e:
        log.exception("❌ Telegram startup check failed: %s", e)
        raise
    reschedule_jobs(app)
    log.info("✅ Jobs scheduled")

def main():
    """Start the bot reliably on Render using long-polling.

    Polling is deliberately used here: Telegram update delivery does not
    depend on Render's webhook URL, proxy, or WEBHOOK_SECRET configuration.
    """
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    if OWNER_ID <= 0:
        log.warning("⚠️ OWNER_ID is not set; owner-only admin commands will be unavailable")

    init_db()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_error_handler(bot_error_handler)

    exempt_commands = {"start", "help", "cancel", "admin"}
    for cmd, fn in [
        ("start", start), ("app", app_cmd), ("help", help_cmd), ("admin", admin_cmd), ("support", support_cmd), ("cancel", cancel_cmd), ("instamart", instamart_command), ("forceadd", forceadd), ("forcedisable", forcedisable),
        ("mode", mode_cmd), ("addchannel", addchannel), ("delchannel", delchannel),
        ("addq", addq), ("set", set_cmd), ("settime", settime_cmd),
        ("addadmin", addadmin), ("removeadmin", removeadmin), ("userinfo", userinfo),
        ("ban", ban), ("unban", unban), ("gift", gift), ("reply", reply_doubt),
        ("addquote", addquote), ("delquote", delquote), ("listquotes", listquotes),
        ("addmeme", addmeme), ("delmeme", delmeme), ("listmemes", listmemes),
        ("addpyq", addpyq)
    ]:
        if cmd in exempt_commands:
            handler_fn = fn
        else:
            async def guarded_command(update, context, _fn=fn):
                uid = update.effective_user.id
                if not is_admin(uid):
                    missing = await force_join_check(context.bot, uid)
                    if missing:
                        await force_join_prompt(update, context, missing)
                        return
                await _fn(update, context)

            handler_fn = guarded_command
        app.add_handler(CommandHandler(cmd, handler_fn))

    for pat, fn in [
        ("^a_app_missing$", app_missing_cb), ("^cls_", class_cb),
        ("^tech_", technique_cb), ("^sess_pause_", session_pause_cb),
        ("^sess_resume_", session_resume_cb), ("^sess_stop_", session_stop_cb),
        ("^sub_", subject_cb), ("^dur_", duration_cb), ("^ans_", answer_cb),
        ("^dq_", daily_quiz_answer), ("^setm_", set_mode_cb),
        ("^support_new$", support_callback), ("^ticket_(reply|close):\\d+$", support_callback), ("^force_verify$", force_verify_cb),
        ("^a_fj", fj_toggle), ("^a_", admin_cb)
    ]:
        if pat == "^force_verify$":
            handler_fn = fn
        else:
            async def guarded_callback(update, context, _fn=fn):
                query = update.callback_query
                uid = query.from_user.id
                if not is_admin(uid):
                    missing = await force_join_check(context.bot, uid)
                    if missing:
                        await query.answer("Pehle required channel(s) join karo.", show_alert=True)
                        await force_join_prompt(update, context, missing)
                        return
                await _fn(update, context)

            handler_fn = guarded_callback
        app.add_handler(CallbackQueryHandler(handler_fn, pattern=pat))

    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_router))
    app.add_handler(MessageHandler(filters.PHOTO, msg_router))

    log.info("🤖 Bhushan Science Bot starting in POLLING mode")
    log.info("📡 Telegram update handlers registered")

    # Polling avoids webhook conflicts/configuration issues. Render's web
    # process still needs an HTTP listener for health checks, so keep Flask
    # alive in a daemon thread while python-telegram-bot polls Telegram.
    port = int(os.environ.get("PORT", "10000"))
    threading.Thread(target=run_web, daemon=True, name="health-server").start()

    # Keep the service alive if Telegram temporarily reports a conflict.
    # A stale webhook is already cleared in post_init; transient Telegram
    # conflicts should not permanently kill the Render process.
    while True:
        try:
            app.run_polling(
                drop_pending_updates=False,
                allowed_updates=Update.ALL_TYPES,
                close_loop=False,
            )
            break
        except Conflict as e:
            log.error("⚠️ Telegram polling conflict: %s; retrying in 10s", e)
            time.sleep(10)
        except Exception as e:
            log.exception("❌ Polling stopped unexpectedly: %s; retrying in 10s", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
