# ============================================================
# BHUSHAN SCIENCE BOT - v3.2 (Render Perfect + Logged)
# ============================================================

import os, sqlite3, logging, asyncio, random, threading, traceback, time, re
from html import escape
from urllib.request import Request, urlopen
from datetime import datetime, timedelta, date, time as dtime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import Conflict
from flask import Flask
import pytz

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
DB_FILE = "bhushan_science.db"
TIMEZONE = "Asia/Kolkata"

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
    "serious": {"name": "🎯 Serious", "start": "✅ Session started.", "break_msg": "⏸️ <b>Break Time</b>", "nag": ["⚠️ Reply karo.", "⏰ Waqt gaya.", "📢 Points katenge."], "reward": "🎉 Shabash!", "punish": "❌ Session fail."},
    "fun": {"name": "😄 Fun", "start": "🚀 Chalo shuru!", "break_msg": "☕ <b>Break!</b>", "nag": ["😂 Utho!", "👀 Reply karo!", "🎈 Focus!"], "reward": "🥳 Topper banega!", "punish": "🙃 Next time pakka!"},
    "laparwah": {"name": "😈 Laparwah", "start": "😤 <b>Chal be, padhna hai.</b>", "break_msg": "😏 <b>Break.</b>", "nag": ["🖕 Uth ja!", "😡 Kahan bhaag gaya?", "🤬 Reply kar!", "😤 Ma ko bata dunga.", "💀 Last warning."], "reward": "💪 <b>Chal be shabash!</b>", "punish": "🤡 <b>Dekh liya?</b> -30 points."},
}

# ================== INDIAN NURSING / NORCET CURRICULUM ==================
# Based on INC's Revised B.Sc. Nursing curriculum (2020) and Revised GNM
# curriculum, which are the nursing-course syllabi relevant to NORCET eligibility.
# NORCET itself tests the nursing-course syllabus at the candidate's essential
# qualification level; it is not a separate INC syllabus. AIIMS also specifies
# General Knowledge & Aptitude for Stage I and nursing-course syllabus for the
# nursing portion.
INC_BSC_SYLLABUS_URL = "https://indiannursingcouncil.org/uploads/pdf/162581803399632881260e803b133fde.pdf"
INC_GNM_SYLLABUS_URL = "https://indiannursingcouncil.org/uploads/pdf/16777602713172325806400970f3f105.pdf"

NORCET_BSC_SUBJECTS = [
    "Communicative English", "Applied Anatomy", "Applied Physiology",
    "Applied Sociology", "Applied Psychology", "Nursing Foundations I",
    "Applied Biochemistry", "Applied Nutrition and Dietetics",
    "Nursing Foundations II", "Health/Nursing Informatics & Technology",
    "Applied Microbiology & Infection Control including Safety",
    "Pharmacology I", "Pathology I",
    "Adult Health (Medical-Surgical) Nursing I with Integrated Pathophysiology",
    "Pharmacology II", "Pathology II & Genetics",
    "Adult Health Nursing II with Integrated Pathophysiology including Geriatric Nursing",
    "Professionalism, Professional Values & Ethics including Bioethics",
    "Child Health Nursing I", "Mental Health Nursing I",
    "Community Health Nursing I including Environmental Science & Epidemiology",
    "Educational Technology / Nursing Education",
    "Introduction to Forensic Nursing & Indian Laws", "Child Health Nursing II",
    "Mental Health Nursing II", "Nursing Management & Leadership",
    "Midwifery / Obstetrics & Gynecology Nursing I", "Community Health Nursing II",
    "Nursing Research & Statistics", "Midwifery / Obstetrics & Gynecology Nursing II",
    "Internship / Intensive Practicum / Residency Posting",
    "Mandatory Modules: First Aid, BCLS, Health Assessment, Palliative Care, Essential Newborn Care (ENBC), FBNBC, IMNCI, PLS/PALS, Safe Delivery",
]

NORCET_GNM_SUBJECTS = [
    "Bio-Science: Anatomy & Physiology", "Microbiology",
    "Behavioural Sciences: Psychology & Sociology",
    "Nursing Foundations / Fundamentals of Nursing", "First Aid",
    "Community Health Nursing I", "Environmental Hygiene",
    "Health Education & Communication Skills", "Nutrition", "English",
    "Computer Education", "Medical-Surgical Nursing I",
    "Medical-Surgical Nursing II", "Mental Health Nursing",
    "Child Health Nursing", "Midwifery", "Gynaecological Nursing",
    "Community Health Nursing II", "Nursing Education",
    "Introduction to Research", "Professional Trends & Adjustment",
    "Nursing Administration & Ward Management", "Clinical / Internship Training",
]

NORCET_SUBJECT_MAP = {}
for _i, _s in enumerate(NORCET_BSC_SUBJECTS): NORCET_SUBJECT_MAP[f"B{_i}"] = _s
for _i, _s in enumerate(NORCET_GNM_SUBJECTS): NORCET_SUBJECT_MAP[f"G{_i}"] = _s

# ================== SUBJECT INDEX / HIGH-YIELD CONTENT ==================
NORCET_INDEX_OVERRIDES = {
    "Communicative English": ["Grammar & sentence structure","Tenses & subject-verb agreement","Articles, prepositions & conjunctions","Vocabulary, synonyms & antonyms","Comprehension","Medical terminology","Precis / communication","Common error spotting"],
    "Applied Anatomy": ["Anatomical terminology & planes","Cells, tissues & membranes","Skeletal system & joints","Muscular system","Cardiovascular system","Respiratory system","Digestive system","Urinary system","Nervous system & special senses","Endocrine system","Reproductive system","Lymphatic system"],
    "Applied Physiology": ["Cell physiology & homeostasis","Blood & immunity","Cardiac cycle & circulation","Respiratory physiology","GIT & digestion","Renal physiology & fluid balance","Nervous system","Endocrine physiology","Reproductive physiology","Temperature regulation & exercise"],
    "Applied Sociology": ["Society & culture","Socialization","Family & marriage","Social groups","Social stratification","Community & social change","Health and illness in society","Indian social problems","Social determinants of health"],
    "Applied Psychology": ["Introduction to psychology","Learning","Memory","Intelligence","Motivation & emotion","Personality","Developmental psychology","Stress & coping","Psychological assessment","Mental health basics"],
    "Nursing Foundations I": ["Nursing profession & history","Nursing process","Basic needs & comfort","Admission, transfer & discharge","Vital signs","Hygiene & personal care","Bed making & positioning","Safety & mobility","Infection prevention","Documentation & reporting","Basic procedures & asepsis"],
    "Applied Biochemistry": ["Carbohydrates","Proteins & amino acids","Lipids","Enzymes","Vitamins & minerals","Nucleic acids","Metabolism","Acid-base balance","Clinical biochemistry","Liver & renal function tests"],
    "Applied Nutrition and Dietetics": ["Nutrients & energy","Balanced diet","Therapeutic diets","Malnutrition","Infant & child nutrition","Pregnancy & lactation nutrition","Enteral & parenteral nutrition","Diet planning","Food hygiene","Nutrition education"],
    "Nursing Foundations II": ["Health assessment","Physical examination","Pain assessment","Medication basics","Fluid & electrolyte care","Oxygen therapy","Wound care","Specimen collection","Perioperative basics","Emergency nursing basics"],
    "Health/Nursing Informatics & Technology": ["Health information systems","Electronic health records","Nursing documentation","Data privacy & security","Telehealth","Digital health tools","Evidence retrieval","Basic statistics/data handling","Technology in patient safety"],
    "Applied Microbiology & Infection Control including Safety": ["Microorganisms","Bacteria, viruses, fungi & parasites","Chain of infection","Standard precautions","Hand hygiene","PPE","Sterilization & disinfection","Biomedical waste","Healthcare-associated infections","Isolation precautions","Needle-stick prevention"],
    "Pharmacology I": ["General pharmacology","Pharmacokinetics & pharmacodynamics","Routes of administration","Adverse drug reactions","Drug interactions","Autonomic drugs","CNS drugs","Cardiovascular drugs","Respiratory drugs","GI drugs","Safe medication administration"],
    "Pathology I": ["Cell injury","Inflammation","Healing & repair","Neoplasia","Hemodynamic disorders","Infectious disease pathology","Hematology basics","Laboratory diagnosis","Specimen handling"],
    "Adult Health (Medical-Surgical) Nursing I with Integrated Pathophysiology": ["Health assessment of adults","Respiratory disorders","Cardiovascular disorders","GI & hepatobiliary disorders","Renal & urinary disorders","Neurological disorders","Endocrine disorders","Musculoskeletal disorders","Perioperative nursing","Emergency & critical care basics","Fluid/electrolyte management"],
    "Pharmacology II": ["Antimicrobials","Endocrine drugs","Chemotherapy","Blood & coagulation drugs","Emergency drugs","Obstetric drugs","Paediatric considerations","Drug calculations","High-alert medications","Fundamentals of prescribing"],
    "Pathology II & Genetics": ["Clinical pathology","Hematology","Immunopathology","Organ-system pathology","Genetic principles","Chromosomal disorders","Genetic counselling","Prenatal diagnosis","Laboratory interpretation"],
    "Adult Health Nursing II with Integrated Pathophysiology including Geriatric Nursing": ["Oncology nursing","Neurological nursing","Renal nursing","Endocrine nursing","Musculoskeletal nursing","Burns & wounds","Geriatric assessment","Dementia & delirium","Palliative care","Rehabilitation","Long-term care"],
    "Professionalism, Professional Values & Ethics including Bioethics": ["Professional identity","Nursing code of ethics","Patient rights","Confidentiality","Consent","Legal responsibilities","Ethical principles","Bioethics","Professional boundaries","Incident reporting"],
    "Child Health Nursing I": ["Growth & development","Paediatric assessment","Newborn care","Nutrition in children","Immunization","Common childhood illnesses","Respiratory disorders","GI disorders","Fluid/electrolyte care","Family-centred care"],
    "Mental Health Nursing I": ["Mental health concepts","Therapeutic communication","Mental status examination","Psychiatric history","Anxiety disorders","Mood disorders","Schizophrenia","Substance use","Suicide risk","Psychiatric emergencies"],
    "Community Health Nursing I including Environmental Science & Epidemiology": ["Community assessment","Primary health care","Health promotion","Epidemiology","Screening","Communicable diseases","Environmental sanitation","Water & air pollution","Waste management","National health programmes"],
    "Educational Technology / Nursing Education": ["Teaching-learning process","Learning theories","Lesson planning","Teaching methods","AV aids","Clinical teaching","Evaluation","Curriculum basics","Student guidance"],
    "Introduction to Forensic Nursing & Indian Laws": ["Forensic nursing role","Medico-legal cases","Evidence preservation","Injury documentation","Consent & confidentiality","Death & dying","Sexual assault care","Poisoning basics","Indian legal framework","Court testimony"],
    "Child Health Nursing II": ["Paediatric emergencies","Congenital disorders","Neurological disorders","Cardiac disorders","Renal disorders","Endocrine disorders","Oncology in children","Hematological disorders","Disability & rehabilitation","Paediatric critical care"],
    "Mental Health Nursing II": ["Psychiatric therapies","Psychopharmacology","ECT","Behaviour therapy","Cognitive therapies","Child/adolescent psychiatry","Geriatric psychiatry","Community mental health","Rehabilitation","Psychiatric nursing care plans"],
    "Nursing Management & Leadership": ["Management principles","Leadership styles","Staffing","Scheduling","Delegation","Supervision","Quality assurance","Nursing audit","Conflict management","Inventory management","Disaster management"],
    "Midwifery / Obstetrics & Gynecology Nursing I": ["Reproductive anatomy","Antenatal care","Normal pregnancy","Labour & delivery","Partograph","Postnatal care","Newborn care","Breastfeeding","Family planning","Obstetric emergencies"],
    "Community Health Nursing II": ["Community diagnosis","Family health nursing","Home visits","School health","Occupational health","National programmes","Maternal & child health","Epidemiological surveillance","Health education","Primary/secondary/tertiary care"],
    "Nursing Research & Statistics": ["Research process","Research designs","Problem & objectives","Literature review","Sampling","Data collection","Validity & reliability","Descriptive statistics","Probability & tests","Research ethics"],
    "Midwifery / Obstetrics and Gynecology (OBG) Nursing II": ["High-risk pregnancy","Hypertensive disorders","Diabetes in pregnancy","Obstetric haemorrhage","Abnormal labour","Operative obstetrics","Puerperal complications","Gynaecological disorders","Infertility","Family planning & reproductive health"],
    "Midwifery / Obstetrics & Gynecology Nursing II": ["High-risk pregnancy","Hypertensive disorders","Diabetes in pregnancy","Obstetric haemorrhage","Abnormal labour","Operative obstetrics","Puerperal complications","Gynaecological disorders","Infertility","Family planning & reproductive health"],
    "Internship / Intensive Practicum / Residency Posting": ["Clinical assessment","Medication safety","Infection control","Documentation","Patient education","Emergency response","Team communication","Care planning","Case presentation","Professional practice"],
    "Mandatory Modules: First Aid, BCLS, Health Assessment, Palliative Care, Essential Newborn Care (ENBC), FBNBC, IMNCI, PLS/PALS, Safe Delivery": ["First Aid & emergency response","BCLS","Health assessment","Palliative care","Essential Newborn Care (ENBC)","Facility Based Newborn Care (FBNBC)","IMNCI","PLS/PALS concepts","Safe delivery practices"],
    "Bio-Science: Anatomy & Physiology": ["Anatomical terminology","Cells & tissues","Skeletal & muscular systems","Cardiovascular system","Respiratory system","Digestive system","Urinary system","Nervous system","Endocrine system","Reproductive system"],
    "Microbiology": ["Microorganisms","Bacteria","Viruses","Fungi","Parasites","Normal flora","Chain of infection","Specimen collection","Sterilization & disinfection","Infection prevention"],
    "Behavioural Sciences: Psychology & Sociology": ["Psychology basics","Learning & memory","Personality","Motivation","Stress & coping","Society & culture","Family","Socialization","Social determinants of health"],
    "Nursing Foundations / Fundamentals of Nursing": ["Nursing process","Vital signs","Hygiene","Bed making","Positioning","Asepsis","Infection control","Medication basics","Documentation","First aid"],
    "First Aid": ["Primary survey","CPR/BLS basics","Bleeding & shock","Fractures","Burns","Poisoning","Choking","Seizures","Emergency transport","Disaster first response"],
    "Community Health Nursing I": ["Community assessment","Primary health care","Health promotion","Family health","Communicable diseases","Maternal-child health","National programmes","Health education","Home visits"],
    "Environmental Hygiene": ["Water sanitation","Air pollution","Waste disposal","Food hygiene","Housing","Vector control","Personal hygiene","Environmental health hazards"],
    "Health Education & Communication Skills": ["Communication process","Therapeutic communication","Health education principles","Individual teaching","Group teaching","AV aids","Counselling","Barriers to communication"],
    "Nutrition": ["Nutrients","Balanced diet","Deficiency diseases","Therapeutic diets","Infant nutrition","Pregnancy nutrition","Food hygiene","Meal planning"],
    "English": ["Grammar","Tenses","Vocabulary","Comprehension","Sentence correction","Synonyms & antonyms","Medical terminology","Communication"],
    "Computer Education": ["Computer basics","Operating systems","Word processing","Spreadsheets","Presentations","Internet & email","Health information systems","Data safety"],
    "Medical-Surgical Nursing I": ["Assessment","Respiratory disorders","Cardiovascular disorders","GI disorders","Renal disorders","Neurological disorders","Endocrine disorders","Infection care","Perioperative care"],
    "Medical-Surgical Nursing II": ["Oncology","Neurology","Renal","Endocrine","Musculoskeletal","Burns","Geriatric nursing","Critical care","Rehabilitation","Palliative care"],
    "Mental Health Nursing": ["Mental health concepts","Therapeutic communication","MSE","Schizophrenia","Mood disorders","Anxiety","Substance use","Suicide prevention","Psychiatric emergencies"],
    "Child Health Nursing": ["Growth & development","Newborn care","Immunization","Common childhood diseases","Nutrition","Paediatric emergencies","Congenital disorders","Family-centred care"],
    "Midwifery": ["Pregnancy","Antenatal care","Labour","Partograph","Delivery","Postnatal care","Newborn care","Breastfeeding","Obstetric emergencies"],
    "Gynaecological Nursing": ["Menstrual disorders","Reproductive tract infections","Infertility","Benign gynaecological disorders","Gynaecological cancers","Contraception","Menopause","Perioperative care"],
    "Community Health Nursing II": ["Community diagnosis","Family health","Home visits","School health","Occupational health","National programmes","MCH","Surveillance","Health education"],
    "Nursing Education": ["Teaching-learning","Lesson plan","Teaching methods","AV aids","Clinical teaching","Evaluation","Curriculum"],
    "Introduction to Research": ["Research problem","Objectives","Literature review","Research designs","Sampling","Data collection","Analysis","Research ethics"],
    "Professional Trends & Adjustment": ["Professional roles","Ethics","Registration","Career development","Stress management","Teamwork","Professional adjustment"],
    "Nursing Administration & Ward Management": ["Ward organization","Staffing","Scheduling","Delegation","Supervision","Records","Inventory","Quality assurance","Leadership"],
    "Clinical / Internship Training": ["Patient assessment","Nursing care plans","Medication safety","Infection control","Documentation","Emergency care","Patient education","Teamwork","Professional conduct"],
}
def norcet_subject_index(subject):
    if subject in NORCET_INDEX_OVERRIDES: return NORCET_INDEX_OVERRIDES[subject]
    s = subject.lower()
    for key, topics in NORCET_INDEX_OVERRIDES.items():
        if key.lower() in s or s in key.lower(): return topics
    return ["Core concepts","Definitions & terminology","Assessment","Pathophysiology / principles","Nursing management","Patient safety","Common complications","Emergency care","Prevention & health education","NORCET high-yield revision"]

def norcet_subject_info(subject):
    topics = norcet_subject_index(subject)
    index_text = "\n".join(f"{i+1}. {x}" for i, x in enumerate(topics))
    # Every clinical topic follows one consistent nursing/NORCET study framework.
    framework = [
        "1️⃣ Definition / Introduction",
        "2️⃣ Causes / Etiology / Risk factors",
        "3️⃣ Pathophysiology / Pathogenesis",
        "4️⃣ Signs & Symptoms / Clinical features",
        "5️⃣ Diagnosis / Diagnostic techniques & investigations",
        "6️⃣ Medical management",
        "7️⃣ Surgical management",
        "8️⃣ Pharmacological management",
        "9️⃣ Nursing management",
        "🔟 Lifestyle modification / Diet / Prevention",
        "1️⃣1️⃣ Nursing Care Plan: Assessment → Nursing Diagnosis → Goals → Interventions → Rationale → Evaluation",
        "1️⃣2️⃣ Nurse Responsibility: monitoring, medication safety, infection control, patient education, documentation, escalation & emergency response",
        "1️⃣3️⃣ Complications / Red flags / When to escalate",
        "1️⃣4️⃣ NORCET high-yield points + case-scenario priorities",
    ]
    important = [
        "⭐ Har disease me definition, etiology, pathophysiology aur clinical features ko connect karke padho.",
        "⭐ Diagnosis me first-line/common tests, important findings aur nursing preparation/after-care yaad rakho.",
        "⭐ Management ko medical + surgical + pharmacological + nursing + lifestyle buckets me revise karo.",
        "⭐ Nursing care plan me NANDA-style nursing diagnosis, measurable goals, interventions, rationale aur evaluation cover karo.",
        "⭐ Nurse responsibility me assessment, vitals, I/O, medication safety, infection prevention, education, documentation aur timely referral/escalation include karo.",
        "⭐ Case-based NORCET question me ABC, priority, safety, red flags aur first nursing action identify karo.",
    ]
    quote = random.choice([
        "🔥 Aaj ka 30 minute kal ki tension kam karta hai.",
        "🧠 Read less, recall more.",
        "💪 Consistency boring hoti hai, result boring nahi.",
        "😂 Notes kholne ka notification aa gaya… ab ignore mat karna.",
        "😄 Coffee optional, revision compulsory.",
    ])
    return (
        f"<b>📚 SUBJECT INDEX</b>\n<b>{escape(subject)}</b>\n\n"
        f"{escape(index_text)}\n\n"
        "<b>🩺 COMPLETE TOPIC FRAMEWORK</b>\n" +
        "\n".join(framework) +
        "\n\n<b>⭐ IMPORTANT</b>\n" + "\n".join(important) +
        f"\n\n<b>💬 QUOTE / MEME</b>\n{quote}" +
        "\n\n📌 INC curriculum + NORCET nursing-course level."
    )

def norcet_subject_info_kb(code):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start Study", callback_data=f"nstart_{code}")],
        [InlineKeyboardButton("🔙 Subject List", callback_data=f"nback_{code[:1]}")],
    ])


def norcet_track_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 INC B.Sc Nursing 2020", callback_data="ntrack_B")],
        [InlineKeyboardButton("🏥 INC GNM 3-Year", callback_data="ntrack_G")],
        [InlineKeyboardButton("📜 INC B.Sc Official Syllabus", url=INC_BSC_SYLLABUS_URL)],
        [InlineKeyboardButton("📜 INC GNM Official Syllabus", url=INC_GNM_SYLLABUS_URL)],
    ])


def norcet_subject_kb(track):
    prefix = "B" if track == "B" else "G"
    subjects = NORCET_BSC_SUBJECTS if track == "B" else NORCET_GNM_SUBJECTS
    rows, row = [], []
    for i, subject in enumerate(subjects):
        row.append(InlineKeyboardButton(subject[:45], callback_data=f"subn_{prefix}{i}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    return InlineKeyboardMarkup(rows)

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
    cur.execute('''CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, topic TEXT, question TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT, correct_option TEXT, explanation TEXT, difficulty TEXT, class_level TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, subject TEXT, technique TEXT, mode TEXT, planned_minutes INTEGER, actual_minutes INTEGER DEFAULT 0, start_time TIMESTAMP, end_time TIMESTAMP, status TEXT DEFAULT 'running', q_asked INTEGER DEFAULT 0, q_correct INTEGER DEFAULT 0, photo_file_id TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS doubts(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, subject TEXT, question_text TEXT, photo_file_id TEXT, answer TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS points_log(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, points INTEGER, reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS quotes(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, author TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS memes(id INTEGER PRIMARY KEY AUTOINCREMENT, file_id TEXT, caption TEXT, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS badges(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, badge_key TEXT, unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, badge_key))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS exam_dates(user_id INTEGER PRIMARY KEY, exam_name TEXT, exam_date DATE, set_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS daily_quiz(id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_date DATE UNIQUE, question TEXT, option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT, correct_option TEXT, explanation TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS quiz_answers(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, quiz_date DATE, chosen TEXT, correct INTEGER, UNIQUE(user_id, quiz_date))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)''')
    defaults = {'force_join_enabled': '1', 'reward_points': '10', 'punishment_points': '20', 'nag_message_count': '5', 'daily_points_target': '50', 'bot_name': 'Bhushan Science', 'welcome_msg': 'Padhai karo!', 'quote_time': '07:00', 'meme_time': '21:00', 'quiz_time': '20:00', 'break_reminder': '1'}
    for k, v in defaults.items(): cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
    try:
        cur.execute("ALTER TABLE users ADD COLUMN last_active TIMESTAMP")
    except sqlite3.OperationalError:
        pass
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
def get_user_mode(uid): u = get_user(uid); return (u.get('mode') if u else None) or 'serious'

# ================== FORCE JOIN ==================
async def check_joined(context, user_id):
    if get_setting('force_join_enabled') != '1': return True
    chs = all_channels()
    if not chs: return True
    for ch in chs:
        try:
            m = await context.bot.get_chat_member(chat_id=ch['channel_id'], user_id=user_id)
            if m.status in ['left', 'kicked']: return False
        except Exception as e: log.warning(f"Join check fail: {e}")
    return True

async def force_join_message(update, context):
    chs = all_channels()
    if not chs: await update.message.reply_text("Koi channel set nahi hai."); return
    btns = [[InlineKeyboardButton(f"📢 {ch['channel_name']}", url=ch['channel_link'])] for ch in chs]
    btns.append([InlineKeyboardButton("✅ Verify Kiya", callback_data="verify_join")])
    await update.message.reply_text("🔒 <b>Pehle channel join karo:</b>", reply_markup=InlineKeyboardMarkup(btns), parse_mode=ParseMode.HTML)

# ================== KEYBOARDS ==================
def main_menu_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📚 Padhai Shuru"), KeyboardButton("📸 Doubt Clear")],
        [KeyboardButton("🎯 Exam Countdown"), KeyboardButton("📅 Aaj ka Target")],
        [KeyboardButton("🏆 Points"), KeyboardButton("🏅 Leaderboard"), KeyboardButton("🎖️ Badges")],
        [KeyboardButton("🎭 Mode Badlo"), KeyboardButton("📊 Report")],
        [KeyboardButton("💭 Thought"), KeyboardButton("😂 Meme"), KeyboardButton("❓ Help")]
    ], resize_keyboard=True)

def admin_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users", callback_data="a_users"), InlineKeyboardButton("📢 Channels", callback_data="a_channels")],
        [InlineKeyboardButton("❓ Questions", callback_data="a_questions"), InlineKeyboardButton("⚙️ Settings", callback_data="a_settings")],
        [InlineKeyboardButton("💭 Quotes", callback_data="a_quotes"), InlineKeyboardButton("😂 Memes", callback_data="a_memes")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="a_broadcast"), InlineKeyboardButton("💬 Doubts", callback_data="a_doubts")],
        [InlineKeyboardButton("🎯 Daily Quiz", callback_data="a_dq"), InlineKeyboardButton("⏰ Times", callback_data="a_times")],
        [InlineKeyboardButton("📊 Stats", callback_data="a_stats"), InlineKeyboardButton("👤 Admins", callback_data="a_admins")],
        [InlineKeyboardButton("🛡️ Ban/Unban", callback_data="a_ban"), InlineKeyboardButton("🎁 Gift Points", callback_data="a_gift")],
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = update.effective_user.first_name or "Student"
    touch_user(uid)
    create_user(uid, name)
    if not await check_joined(context, uid): await force_join_message(update, context); return
    user = get_user(uid)
    if not user.get('verified'): update_user(uid, verified=1)
    if not user.get('user_class'):
        await update.message.reply_text(f"👋 Namaste <b>{name}</b>!\n\nMain <b>{get_setting('bot_name')}</b> hoon.\n\nApni class batao:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Class 9", callback_data="cls_9"), InlineKeyboardButton("Class 10", callback_data="cls_10")], [InlineKeyboardButton("Class 11", callback_data="cls_11"), InlineKeyboardButton("Class 12", callback_data="cls_12")], [InlineKeyboardButton("NEET", callback_data="cls_NEET"), InlineKeyboardButton("NORCET", callback_data="cls_NORCET")], [InlineKeyboardButton("Other", callback_data="cls_Other")]]))
        return
    mode_n = MODES.get(user.get('mode', 'serious'), MODES['serious'])['name']
    await update.message.reply_text(f"✅ Welcome <b>{name}</b>!\n\n💎 Points: <b>{user['points']}</b>\n🔥 Streak: <b>{user['streak']} din</b>\n⏱ Total: <b>{user['total_minutes']} min</b>\n🎭 Mode: <b>{mode_n}</b>\n\n📌 {get_setting('welcome_msg')}", parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())

async def verify_join_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if await check_joined(context, q.from_user.id): await q.edit_message_text("✅ Verified! Ab /start dabao.")
    else: await q.edit_message_text("❌ Saare channels join karo.")

async def class_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id); cls = q.data.replace("cls_", "")
    update_user(q.from_user.id, user_class=cls)
    if cls == "NORCET":
        context.user_data['norcet_track'] = None
        await q.edit_message_text(
            "🇮🇳 <b>NORCET Syllabus</b>\n\n"
            "INC ke nursing curriculum ke according preparation track chuno.\n"
            "NORCET mein nursing portion candidate ki essential qualification ke nursing-course syllabus par based hota hai.",
            parse_mode=ParseMode.HTML,
            reply_markup=norcet_track_kb()
        )
        return
    await q.edit_message_text(f"✅ Class: <b>{cls}</b>", parse_mode=ParseMode.HTML)
    await context.bot.send_message(q.from_user.id, "Ab padhai shuru karo 👇", reply_markup=main_menu_kb())

async def norcet_track_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id)
    track = q.data.replace("ntrack_", "")
    context.user_data['norcet_track'] = track
    name = "INC B.Sc Nursing 2020" if track == "B" else "INC GNM 3-Year"
    subjects = NORCET_BSC_SUBJECTS if track == "B" else NORCET_GNM_SUBJECTS
    await q.edit_message_text(
        f"📚 <b>{name}</b>\n\n"
        f"Total subjects/modules: <b>{len(subjects)}</b>\n"
        "Subject select karo:",
        parse_mode=ParseMode.HTML,
        reply_markup=norcet_subject_kb(track)
    )

async def norcet_subject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id)
    code = q.data.replace("subn_", "")
    subject = NORCET_SUBJECT_MAP.get(code, "General Nursing")
    context.user_data['subject'] = subject
    context.user_data['norcet_subject_code'] = code
    await q.edit_message_text(
        f"🇮🇳 <b>{escape(subject)}</b>\n\n{norcet_subject_info(subject)}",
        parse_mode=ParseMode.HTML,
        reply_markup=norcet_subject_info_kb(code)
    )

async def norcet_back_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id)
    track = q.data.replace("nback_", "")
    await q.edit_message_text(
        "📚 <b>Subject List</b>\n\nSubject select karo:",
        parse_mode=ParseMode.HTML,
        reply_markup=norcet_subject_kb(track)
    )

async def norcet_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id)
    code = q.data.replace("nstart_", "")
    subject = NORCET_SUBJECT_MAP.get(code, context.user_data.get('subject', 'General Nursing'))
    context.user_data['subject'] = subject
    default = TECHNIQUES[context.user_data.get('technique', 'pomodoro')]['work'] * TECHNIQUES[context.user_data.get('technique', 'pomodoro')]['cycles']
    context.user_data['duration'] = default
    await q.edit_message_text(
        f"🇮🇳 <b>{escape(subject)}</b>\n\n⏱ Default: <b>{default} min</b>\n\nDuration choose karo:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Default ({default}m)", callback_data=f"dur_{default}"), InlineKeyboardButton("30 min", callback_data="dur_30")],
            [InlineKeyboardButton("1 ghanta", callback_data="dur_60"), InlineKeyboardButton("2 ghante", callback_data="dur_120")],
            [InlineKeyboardButton("3 ghante", callback_data="dur_180"), InlineKeyboardButton("Custom", callback_data="dur_custom")]
        ])
    )

# ================== MODE ==================
async def mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = get_user_mode(update.effective_user.id); btns = []
    for k, m in MODES.items(): btns.append([InlineKeyboardButton(f"{'✅ ' if k == cur else ''}{m['name']}", callback_data=f"setm_{k}")])
    await update.message.reply_text("🎭 <b>Apna Mode Chuno</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))

async def set_mode_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); mode = q.data.replace("setm_", "")
    update_user(q.from_user.id, mode=mode)
    await q.edit_message_text(f"✅ Mode: <b>{MODES[mode]['name']}</b>", parse_mode=ParseMode.HTML)

# ================== PADHAI ==================
async def padhai_shuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update.effective_user.id)
    if not await check_joined(context, update.effective_user.id): await force_join_message(update, context); return
    keys = list(TECHNIQUES.keys()); btns = []; row = []
    for k in keys:
        row.append(InlineKeyboardButton(TECHNIQUES[k]['name'], callback_data=f"tech_{k}"))
        if len(row) == 2: btns.append(row); row = []
    if row: btns.append(row)
    await update.message.reply_text("🎓 <b>Technique Chuno</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))

async def technique_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id); tech = q.data.replace("tech_", "")
    context.user_data['technique'] = tech; t = TECHNIQUES[tech]; total = t['work'] * t['cycles']
    user = get_user(q.from_user.id) or {}
    if user.get('user_class') == "NORCET":
        track = context.user_data.get('norcet_track')
        if track:
            await q.edit_message_text(
                f"{t['name']}\n\n{t['desc']}\n\n⏱ {t['work']}min × {t['cycles']} = <b>{total} min</b>\n\n🇮🇳 NORCET subject chuno:",
                parse_mode=ParseMode.HTML,
                reply_markup=norcet_subject_kb(track)
            )
            return
    await q.edit_message_text(f"{t['name']}\\n\\n{t['desc']}\\n\\n⏱ {t['work']}min × {t['cycles']} = <b>{total} min</b>\\n\\nAb subject chuno:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Physics", callback_data="sub_Physics"), InlineKeyboardButton("Chemistry", callback_data="sub_Chemistry")], [InlineKeyboardButton("Biology", callback_data="sub_Biology"), InlineKeyboardButton("Maths", callback_data="sub_Maths")], [InlineKeyboardButton("English", callback_data="sub_English"), InlineKeyboardButton("GK", callback_data="sub_GK")], [InlineKeyboardButton("Other", callback_data="sub_Other")]]))

async def subject_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); sub = q.data.replace("sub_", "")
    context.user_data['subject'] = sub
    default = TECHNIQUES[context.user_data.get('technique', 'pomodoro')]['work'] * TECHNIQUES[context.user_data.get('technique', 'pomodoro')]['cycles']
    await q.edit_message_text(f"Subject: <b>{sub}</b>\n\nKitni der?", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Default ({default}m)", callback_data=f"dur_{default}"), InlineKeyboardButton("30 min", callback_data="dur_30")], [InlineKeyboardButton("1 ghanta", callback_data="dur_60"), InlineKeyboardButton("2 ghante", callback_data="dur_120")], [InlineKeyboardButton("3 ghante", callback_data="dur_180"), InlineKeyboardButton("Custom", callback_data="dur_custom")]]))

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

async def start_study_session(context: ContextTypes.DEFAULT_TYPE, uid):
    sub = context.user_data.get('subject', 'General')
    dur = int(context.user_data.get('duration', 30))
    tech = context.user_data.get('technique', 'pomodoro')
    mode = get_user_mode(uid)
    c = db()
    cur = c.execute("INSERT INTO sessions(user_id,subject,technique,mode,planned_minutes,start_time,photo_file_id,status) VALUES(?,?,?,?,?,?,?,?)",
                    (uid, sub, tech, mode, dur, datetime.now(), None, 'running'))
    sid = cur.lastrowid; c.commit(); c.close()
    update_user(uid, current_session=sid); touch_user(uid)
    u = get_user(uid); used = [x for x in (u.get('techniques_used') or '').split(',') if x]
    if tech not in used: used.append(tech)
    update_user(uid, techniques_used=','.join(used)); check_badges(uid)
    context.user_data['session_id'] = sid
    context.user_data['awaiting'] = None
    t = TECHNIQUES[tech]
    for cyc in range(t['cycles']):
        delay_min = t['work'] * (cyc + 1) + t['break'] * cyc
        if delay_min < dur:
            context.job_queue.run_once(break_msg_job, delay_min * 60, chat_id=uid, data={'sid': sid, 'cycle': cyc + 1, 'mode': mode})
    context.job_queue.run_once(session_reminder, dur * 60, chat_id=uid, data={'sid': sid})
    context.job_queue.run_once(nag_check, (dur + 5) * 60, chat_id=uid, data={'sid': sid})
    await context.bot.send_message(uid, f"✅ <b>Session #{sid}</b>\n\n{t['name']} | {escape(sub)} | {dur} min\n\n{MODES[mode]['start']}\n\n📌 Index + important points dekhne ke baad focused study karo.", parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())


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
    await ask_questions(context, uid, sid)

async def nag_check(context: ContextTypes.DEFAULT_TYPE):
    sid = context.job.data['sid']; uid = context.job.chat_id; u = get_user(uid)
    if not u or u.get('current_session') != sid: return
    mode = get_user_mode(uid); nags = MODES[mode]['nag']; n = int(get_setting('nag_message_count', '5'))
    for i in range(n):
        try: await context.bot.send_message(uid, f"{nags[i % len(nags)]}\n\n({i+1}/{n})")
        except: pass
        await asyncio.sleep(60)
    pts = int(get_setting('punishment_points', '20')); add_points(uid, -pts, f"Session #{sid} adhura")
    c = db(); c.execute("UPDATE sessions SET status='failed', end_time=? WHERE id=?", (datetime.now(), sid)); c.commit(); c.close()
    update_user(uid, current_session=0)
    await context.bot.send_message(uid, f"{MODES[mode]['punish']}\n\nPoints: -{pts}", parse_mode=ParseMode.HTML)

# ================== QUESTIONS ==================
async def ask_questions(context, uid, sid):
    u = get_user(uid); cls = u.get('user_class', 'Other')
    c = db(); rows = c.execute("SELECT * FROM questions WHERE class_level IN (?, 'All') ORDER BY RANDOM() LIMIT 3", (cls,)).fetchall(); c.close()
    if not rows:
        await context.bot.send_message(uid, "✅ Session complete! Question bank empty.")
        await finish_session(context, uid, sid, 0, 0); return
    context.user_data[f'qq_{sid}'] = [dict(r) for r in rows]
    context.user_data[f'qi_{sid}'] = 0; context.user_data[f'qc_{sid}'] = 0
    await context.bot.send_message(uid, f"📝 Session #{sid} time up!\n\nAb 3 questions:")
    await send_next_question(context, uid, sid)

async def send_next_question(context, uid, sid):
    qs = context.user_data.get(f'qq_{sid}', []); i = context.user_data.get(f'qi_{sid}', 0)
    if i >= len(qs): await finish_session(context, uid, sid, len(qs), context.user_data.get(f'qc_{sid}', 0)); return
    q = qs[i]
    btns = [[InlineKeyboardButton(f"{opt.upper()}) {q[f'option_{opt}']}", callback_data=f"ans_{sid}_{opt}")] for opt in ['a','b','c','d'] if q.get(f'option_{opt}')]
    await context.bot.send_message(uid, f"<b>Q{i+1}.</b> {q['question']}", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))

async def answer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); uid = q.from_user.id
    parts = q.data.split("_"); sid = int(parts[1]); chosen = parts[2]
    qs = context.user_data.get(f'qq_{sid}', []); i = context.user_data.get(f'qi_{sid}', 0)
    if i >= len(qs): return
    correct = qs[i].get('correct_option', 'a').lower(); expl = qs[i].get('explanation', '')
    if chosen == correct:
        context.user_data[f'qc_{sid}'] = context.user_data.get(f'qc_{sid}', 0) + 1
        await q.edit_message_text(f"✅ Sahi! {expl}")
    else: await q.edit_message_text(f"❌ Galat. Sahi: <b>{correct.upper()}</b>\n{expl}", parse_mode=ParseMode.HTML)
    context.user_data[f'qi_{sid}'] = i + 1; await asyncio.sleep(1.5); await send_next_question(context, uid, sid)

async def finish_session(context, uid, sid, asked, correct):
    pts = int(get_setting('reward_points', '10')); total_pts = pts + correct * 5
    c = db(); c.execute("UPDATE sessions SET status='completed', end_time=?, q_asked=?, q_correct=? WHERE id=?", (datetime.now(), asked, correct, sid))
    row = c.execute("SELECT planned_minutes FROM sessions WHERE id=?", (sid,)).fetchone(); planned = row['planned_minutes'] if row else 0; c.close()
    u = get_user(uid); total_min = (u['total_minutes'] or 0) + planned
    today = date.today().isoformat(); last = u.get('last_study'); streak = u.get('streak') or 0
    if last == today: pass
    elif last == (date.today() - timedelta(days=1)).isoformat(): streak += 1
    else: streak = 1
    update_user(uid, total_minutes=total_min, streak=streak, last_study=today, current_session=0, sessions_done=(u['sessions_done'] or 0) + 1)
    add_points(uid, total_pts, f"Session #{sid} complete")
    await context.bot.send_message(uid, f"{MODES[get_user_mode(uid)]['reward']}\n\n✅ Sahi: {correct}/{asked}\n💎 +{total_pts} points\n🔥 Streak: {streak} din\n⏱ Total: {total_min} min", parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())

# ================== DOUBT ==================
async def doubt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'doubt_photo'
    await update.message.reply_text("📸 <b>Doubt Clear</b>\n\nPhoto bhejo ya text likho.", parse_mode=ParseMode.HTML)

async def doubt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting') != 'doubt_photo': return
    uid = update.effective_user.id
    if update.message.photo: fid = update.message.photo[-1].file_id; txt = update.message.caption or "[Photo]"
    else: fid = None; txt = update.message.text
    answer = search_answer(txt)
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
    await update.message.reply_text("❓ <b>Help</b>\n\n📚 Padhai Shuru\n📸 Doubt Clear\n🎭 Mode Badlo\n🎯 Exam Countdown\n📊 Report\n🏆 Points\n🏅 Leaderboard\n🎖️ Badges\n💭 Thought / 😂 Meme\n\nCommands: /start /admin /help /mode", parse_mode=ParseMode.HTML)

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
    c = db(); r = c.execute("SELECT text, author FROM quotes ORDER BY RANDOM() LIMIT 1").fetchone(); c.close()
    if not r: await update.message.reply_text("💭 Koi quote nahi."); return
    await update.message.reply_text(f"💭 <b>Thought</b>\n\n<i>{r['text']}</i>\n\n— {r['author']}", parse_mode=ParseMode.HTML)

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
    q = update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): await q.edit_message_text("❌ Not admin."); return
    d = q.data
    if d == "a_menu": await q.edit_message_text("🛠️ Admin Panel", reply_markup=admin_menu_kb()); return
    if d == "a_channels": await channels_panel(q, context); return
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
    btns = []
    if get_setting('force_join_enabled') == '1': btns.append([InlineKeyboardButton("🔓 Force Join OFF", callback_data="a_fjoff")])
    else: btns.append([InlineKeyboardButton("🔒 Force Join ON", callback_data="a_fjon")])
    btns.append([InlineKeyboardButton("🔙 Back", callback_data="a_menu")])
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btns))

async def fj_toggle(update, context):
    q = update.callback_query; await q.answer()
    if q.data == "a_fjon": set_setting('force_join_enabled', '1')
    else: set_setting('force_join_enabled', '0')
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

# ================== ONLINE SOURCE MONITOR ==================
ONLINE_UPDATE_SOURCES = {
    "INC": "https://www.indiannursingcouncil.org/updates",
    "AIIMS": "https://www.aiimsexams.ac.in/",
}
def _online_title(url):
    try:
        req=Request(url,headers={"User-Agent":"BhushanScienceBot/3.2"})
        with urlopen(req,timeout=8) as r: raw=r.read(120000).decode("utf-8","ignore")
        m=re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S)
        return re.sub(r"\s+"," ",m.group(1)).strip() if m else "OK"
    except Exception as e: return f"ERROR: {type(e).__name__}"

async def online_source_update_job(context):
    changes=[]
    for name,url in ONLINE_UPDATE_SOURCES.items():
        title=await asyncio.to_thread(_online_title,url)
        old=get_setting(f"online_{name.lower()}_title")
        if old and old!=title and not title.startswith("ERROR:"): changes.append(f"🔔 {name} source changed")
        set_setting(f"online_{name.lower()}_title",title)
    set_setting("online_last_check",datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if changes and OWNER_ID>0:
        try: await context.bot.send_message(OWNER_ID,"🌐 Online source update detected:\n"+"\n".join(changes))
        except Exception: pass

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

    for name in ["daily_quote", "daily_meme", "daily_quiz", "exam_countdown", "idle_coach", "online_source_update"]:
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
    job_queue.run_repeating(online_source_update_job, interval=120, first=10, name="online_source_update")

# ================== CHANNEL POST ==================
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post
    if not post: return
    try: await context.bot.forward_message(OWNER_ID, post.chat_id, post.message_id)
    except: pass

# ================== ROUTER ==================
async def msg_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid = update.effective_user.id; touch_user(uid); u = get_user(uid)
    if u and u.get('is_banned'): await update.message.reply_text("🚫 Banned."); return
    txt = (update.message.text or "").strip(); aw = context.user_data.get('awaiting')
    if aw == 'custom_minutes': await custom_minutes_msg(update, context); return
    if aw == 'doubt_photo': await doubt_photo(update, context); return
    if aw == 'broadcast': await broadcast_msg(update, context); return
    if aw == 'exam_name': await exam_name_msg(update, context); return
    if aw == 'exam_date': await exam_date_msg(update, context); return
    if aw == 'daily_quiz': await daily_quiz_admin_msg(update, context); return

    if txt == "📚 Padhai Shuru": await padhai_shuru(update, context); return
    if txt == "📸 Doubt Clear": await doubt_start(update, context); return
    if txt == "🎭 Mode Badlo": await mode_menu(update, context); return
    if txt in ("📊 Report", "📊 Meri Report"): await report(update, context); return
    if txt == "🏆 Points": await points_cmd(update, context); return
    if txt == "📅 Aaj ka Target": await today_target(update, context); return
    if txt == "🏅 Leaderboard": await leaderboard(update, context); return
    if txt == "🎖️ Badges": await badges_view(update, context); return
    if txt == "🎯 Exam Countdown": await exam_countdown(update, context); return
    if txt == "💭 Thought": await thought_view(update, context); return
    if txt == "😂 Meme": await meme_view(update, context); return
    if txt == "❓ Help": await help_cmd(update, context); return

# ================== MAIN ==================
async def post_init(app):
    reschedule_jobs(app); log.info("✅ Jobs scheduled")

def main():
    try:
        if not BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN environment variable is not set")

        if OWNER_ID <= 0:
            log.warning("⚠️ OWNER_ID is not set; owner-only admin commands will be unavailable")

        threading.Thread(target=run_web, daemon=True).start()
        log.info("🌐 Web server thread started")
        init_db()
        app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        for cmd, fn in [("start", start), ("help", help_cmd), ("admin", admin_cmd), ("mode", mode_cmd), ("addchannel", addchannel), ("delchannel", delchannel), ("addq", addq), ("set", set_cmd), ("settime", settime_cmd), ("addadmin", addadmin), ("removeadmin", removeadmin), ("userinfo", userinfo), ("ban", ban), ("unban", unban), ("gift", gift), ("reply", reply_doubt), ("addquote", addquote), ("delquote", delquote), ("listquotes", listquotes), ("addmeme", addmeme), ("delmeme", delmeme), ("listmemes", listmemes)]:
            app.add_handler(CommandHandler(cmd, fn))
        for pat, fn in [("^verify_join$", verify_join_cb), ("^cls_", class_cb), ("^ntrack_", norcet_track_cb), ("^subn_", norcet_subject_cb), ("^nstart_", norcet_start_cb), ("^nback_", norcet_back_cb), ("^tech_", technique_cb), ("^sub_", subject_cb), ("^dur_", duration_cb), ("^ans_", answer_cb), ("^dq_", daily_quiz_answer), ("^setm_", set_mode_cb), ("^a_fj", fj_toggle), ("^a_", admin_cb)]:
            app.add_handler(CallbackQueryHandler(fn, pattern=pat))
        app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_router))
        app.add_handler(MessageHandler(filters.PHOTO, msg_router))
        log.info("🤖 Bhushan Science Bot v3.2 starting...")
        # Telegram allows only ONE getUpdates poller per bot token.
        # During Render auto-deploy/restart, the old instance can briefly overlap
        # with the new one and Telegram returns HTTP 409 Conflict. Do not crash;
        # keep this process alive and retry until the other instance disappears.
        first_poll = True
        while True:
            try:
                log.info("📡 Starting Telegram polling...")
                app.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=first_poll,
                    close_loop=False,
                )
                break
            except Conflict as e:
                first_poll = False
                log.warning("⚠️ Telegram polling conflict (another instance is active). Retrying in 10s: %s", e)
                time.sleep(10)
    except Exception as e:
        log.error(f"❌ BOT CRASHED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
