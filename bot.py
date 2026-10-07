        norcet_topic_info(subject, topic),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Important Topics", callback_data=f"nbacktopic_{code}")],
            [InlineKeyboardButton("▶️ Start Study Session", callback_data=f"nstart_{code}")]
        ])
    )

async def norcet_backtopic_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); touch_user(q.from_user.id)
    code = q.data.replace("nbacktopic_", "")
    subject = NORCET_SUBJECT_MAP.get(code, "General Nursing")
    await q.edit_message_text(
        norcet_subject_info(subject),
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
async def padhai_shuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    touch_user(update.effective_user.id)
    user = get_user(update.effective_user.id) or {}
    context.user_data.pop('subject', None)
    if user.get('user_class') == "NORCET":
        track = context.user_data.get('norcet_track')
        if track:
            await update.message.reply_text("🇮🇳 <b>NORCET</b> — Subject chuno:", parse_mode=ParseMode.HTML, reply_markup=norcet_subject_kb(track))
            return
    await update.message.reply_text("📚 <b>Subject chuno</b>", parse_mode=ParseMode.HTML, reply_markup=subject_selection_kb())

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
    jq=app.job_queue
    if not jq: return
    for name in (f"session_break_{sid}",f"session_reminder_{sid}",f"session_nag_{sid}"):
        for job in jq.get_jobs_by_name(name): job.schedule_removal()

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
    u = get_user(uid); cls = u.get('user_class', 'Other')
    c = db(); rows = c.execute("SELECT * FROM questions WHERE class_level IN (?, 'All') AND upper(COALESCE(source,''))='PYQ' ORDER BY RANDOM() LIMIT 3", (cls,)).fetchall(); c.close()
    if not rows:
        await context.bot.send_message(uid, "ℹ️ Timer complete. Is class ke verified PYQs abhi available nahi hain. Session complete mark kiya ja raha hai.")
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
    total_pts = 5
    c = db(); c.execute("UPDATE sessions SET status='completed', end_time=?, q_asked=?, q_correct=? WHERE id=?", (datetime.now(), asked, correct, sid))
    row = c.execute("SELECT planned_minutes FROM sessions WHERE id=?", (sid,)).fetchone(); planned = row['planned_minutes'] if row else 0; c.close()
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
    prompt = """You are Bhushan Science Bot's nursing/science doubt-solving AI.
Read the student's question/image carefully and answer in clear Hinglish/English.
For nursing/medical questions, use: Definition; Causes/Risk factors; Pathophysiology; Signs & Symptoms; Diagnosis/Investigations; Medical management; Surgical management; Pharmacological management; Nursing management; Lifestyle/Diet/Prevention; Nursing Care Plan; Nurse Responsibilities; Complications/Red flags; NORCET high-yield points.
For non-medical questions, answer directly. If image is blurry/unreadable, say so instead of inventing text. Do not claim a diagnosis for a real patient from an image. For urgent symptoms advise medical evaluation."""
    content=[{"type":"text","text":prompt}]
    if question_text and question_text != "[Photo]": content.append({"type":"text","text":"Student question: "+question_text})
    if image_bytes:
        b64=base64.b64encode(image_bytes).decode("ascii")
        content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b64,"detail":"high"}})
    payload={"model":OPENAI_VISION_MODEL,"messages":[{"role":"system","content":"Accurate nursing/science tutor. Never fabricate unreadable information."},{"role":"user","content":content}],"temperature":0.2,"max_tokens":3000}
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

    for name in ["daily_quote", "daily_meme", "daily_quiz", "exam_countdown", "idle_coach", "online_source_update", "auto_meme_publish"]:
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
    try: meme_interval=max(300,int(get_setting("auto_meme_interval","1800") or 1800))
    except: meme_interval=1800
    job_queue.run_repeating(auto_meme_job,interval=meme_interval,first=60,name="auto_meme_publish")

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
    log.info("📩 Incoming Telegram message: user=%s type=%s text=%r", uid, "photo" if update.message.photo else "text", (update.message.text or update.message.caption or "")[:120])
    touch_user(uid); u = get_user(uid)
    if u and u.get('is_banned'): await update.message.reply_text("🚫 Banned."); return
    txt = (update.message.text or "").strip(); aw = context.user_data.get('awaiting')
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
    reschedule_jobs(app); log.info("✅ Jobs scheduled")

def main():
    """
    Production startup.

    Telegram delivery is intentionally WEBHOOK-FIRST.  The previous polling
    deployment could leave an older process consuming getUpdates and replying
    with stale code (for example the legacy A_TOOLSx2 force-join message).
    Webhook mode makes Telegram deliver updates only to this deployment.
    """
    try:
        if not BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN environment variable is not set")

        if OWNER_ID <= 0:
            log.warning("⚠️ OWNER_ID is not set; owner-only admin commands will be unavailable")

        init_db()

        app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        app.add_error_handler(bot_error_handler)

        # Commands
        for cmd, fn in [
            ("start", start), ("app", app_cmd), ("help", help_cmd), ("admin", admin_cmd),
            ("mode", mode_cmd), ("addchannel", addchannel), ("delchannel", delchannel),
            ("addq", addq), ("set", set_cmd), ("settime", settime_cmd),
            ("addadmin", addadmin), ("removeadmin", removeadmin), ("userinfo", userinfo),
            ("ban", ban), ("unban", unban), ("gift", gift), ("reply", reply_doubt),
            ("addquote", addquote), ("delquote", delquote), ("listquotes", listquotes),
            ("addmeme", addmeme), ("delmeme", delmeme), ("listmemes", listmemes), ("addpyq", addpyq)
        ]:
            app.add_handler(CommandHandler(cmd, fn))

        # Callback handlers
        for pat, fn in [
            ("^a_app_missing$", app_missing_cb), ("^cls_", class_cb),
            ("^ntrack_", norcet_track_cb), ("^cterm_", course_term_cb), ("^cpractice_", course_practice_cb), ("^tqa_", topic_answer_cb), ("^csubback_", course_subback_cb),
            ("^csub_", course_subject_cb), ("^ctopic_", course_topic_cb), ("^cstart_", course_start_cb), ("^cback_", course_back_cb),
            ("^subn_", norcet_subject_cb),
            ("^ninfo_", norcet_info_cb), ("^ntech_", norcet_technique_cb),
            ("^ntopic_", norcet_topic_cb), ("^nbacktopic_", norcet_backtopic_cb),
            ("^nstart_", norcet_start_cb), ("^nback_", norcet_back_cb),
            ("^tech_", technique_cb), ("^sess_pause_", session_pause_cb), ("^sess_resume_", session_resume_cb), ("^sess_stop_", session_stop_cb), ("^sub_", subject_cb), ("^dur_", duration_cb),
            ("^ans_", answer_cb), ("^dq_", daily_quiz_answer), ("^setm_", set_mode_cb),
            ("^a_fj", fj_toggle), ("^a_", admin_cb)
        ]:
            app.add_handler(CallbackQueryHandler(fn, pattern=pat))

        # Message handlers
        app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_router))
        app.add_handler(MessageHandler(filters.PHOTO, msg_router))

        log.info("🤖 Bhushan Science Bot v3.2 starting...")
        log.info("📡 Telegram update handlers registered")
        log.info("🛡️ Legacy force-join is disabled in /start")


        # Start the Telegram update receiver. Render supplies PORT and,
        # when available, the public service URL/hostname. Webhook mode is
        # preferred so only this deployment consumes Telegram updates.
        port = int(os.environ.get("PORT", "10000"))
        external_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
        external_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
        if not external_url and external_host:
            external_url = f"https://{external_host}"

        webhook_secret = os.environ.get("WEBHOOK_SECRET", "").strip() or None

        if external_url:
            webhook_url = f"{external_url}/telegram"
            log.info("🌐 Starting Telegram webhook on %s", webhook_url)
            app.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path="telegram",
                webhook_url=webhook_url,
                drop_pending_updates=False,
                secret_token=webhook_secret,
            )
        else:
            # Local/non-Render fallback: polling keeps the bot usable when
            # no public HTTPS endpoint is configured.
            log.warning("⚠️ No RENDER_EXTERNAL_URL/HOSTNAME found; starting polling fallback.")
            app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)

    except Exception:
        log.exception("❌ Fatal bot startup error")
        raise


if __name__ == "__main__":
    main()
