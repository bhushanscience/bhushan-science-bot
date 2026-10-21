(() => {
  "use strict";
  const tg = window.Telegram?.WebApp;
  try { tg?.ready(); tg?.expand(); tg?.setHeaderColor?.("#090b14"); tg?.setBackgroundColor?.("#090b14"); } catch (_) {}

  const STORE_KEY = "bhushan-study-os-v2";
  const quotes = [
    "You don't need to feel ready. You need to begin.",
    "One concept understood beats ten pages skimmed.",
    "Consistency is quiet. The results won't be.",
    "Study for the nurse you want to become.",
    "Progress is built one honest session at a time.",
    "You can restart your focus as many times as you need."
  ];
  const lessons = {
    fundamentals: [
      { title: "Five moments of hand hygiene", time: "3 min read", note: "Hand hygiene is one of the most effective ways to reduce healthcare-associated infections.", points: ["Before touching a patient.", "Before a clean or aseptic procedure.", "After body-fluid exposure risk.", "After touching a patient.", "After touching the patient's surroundings."], takeaway: "Use the appropriate hand-hygiene method and follow your clinical facility's current protocol." },
      { title: "Vital signs: the basics", time: "4 min read", note: "Vital signs help assess a person's current physiological state and identify changes that need attention.", points: ["Temperature reflects body heat regulation.", "Pulse includes rate, rhythm and volume.", "Respiratory assessment includes rate, rhythm and effort.", "Blood pressure reflects arterial pressure.", "Oxygen saturation estimates haemoglobin oxygen saturation."], takeaway: "Interpret observations in context; compare with baseline and local escalation criteria." },
      { title: "Medical asepsis", time: "3 min read", note: "Medical asepsis aims to reduce the number and spread of microorganisms.", points: ["Perform hand hygiene at the correct moments.", "Use clean equipment and keep it clean.", "Follow standard precautions for every patient.", "Handle waste and linen according to policy."], takeaway: "Clean technique reduces contamination; sterile technique is required for specific procedures." }
    ],
    anatomy: [
      { title: "The heart's conduction pathway", time: "4 min read", note: "The cardiac conduction system coordinates electrical activation of the myocardium.", points: ["The sinoatrial node normally initiates the impulse.", "The atrioventricular node briefly delays conduction.", "The impulse travels through the bundle of His.", "Right and left bundle branches conduct toward the ventricles.", "Purkinje fibres distribute the impulse through ventricular muscle."], takeaway: "Electrical activity coordinates contraction; an ECG records electrical signals, not pumping strength directly." },
      { title: "Gas exchange in the lungs", time: "3 min read", note: "Gas exchange occurs across the thin alveolar-capillary membrane.", points: ["Oxygen diffuses from alveoli into pulmonary capillary blood.", "Carbon dioxide diffuses from blood into alveoli.", "Diffusion follows partial-pressure gradients.", "Ventilation and perfusion both affect gas exchange."], takeaway: "Ventilation moves air; perfusion moves blood through the pulmonary circulation." },
      { title: "Nephron: filtration to urine", time: "4 min read", note: "The nephron is the functional unit of the kidney.", points: ["Glomerular filtration moves water and small solutes into the filtrate.", "Tubular reabsorption returns needed substances to blood.", "Tubular secretion moves selected substances into tubular fluid.", "Urine concentration is regulated along the nephron and collecting duct."], takeaway: "Kidneys help regulate fluid, electrolytes, acid-base balance and waste excretion." }
    ],
    pharmacology: [
      { title: "Medication safety checks", time: "4 min read", note: "Medication administration requires a systematic safety check and adherence to local policy.", points: ["Verify the correct patient using approved identifiers.", "Check medication, dose, route and timing.", "Review allergies, contraindications and relevant observations.", "Document administration and response accurately.", "Clarify unclear orders before proceeding."], takeaway: "Never guess an unclear order. Follow current policy and seek an authorised clinician when uncertain." },
      { title: "Pharmacokinetics: ADME", time: "3 min read", note: "Pharmacokinetics describes what the body does to a medicine.", points: ["Absorption: entry into systemic circulation.", "Distribution: movement between blood and tissues.", "Metabolism: chemical transformation, often in the liver.", "Excretion: removal, commonly through the kidneys."], takeaway: "ADME influences onset, duration, interactions and the need for dose adjustment." },
      { title: "Adverse drug reactions", time: "3 min read", note: "An adverse drug reaction is a harmful, unintended response to a medicine used at normal doses.", points: ["Assess and report suspected reactions promptly.", "Prioritise patient safety and urgent clinical assessment.", "Record relevant details according to policy.", "Report through the appropriate pharmacovigilance pathway."], takeaway: "A suspected serious reaction needs prompt clinical escalation; do not independently alter treatment outside your scope." }
    ],
    community: [
      { title: "Levels of prevention", time: "3 min read", note: "Prevention can be organised by when action occurs in relation to disease.", points: ["Primary prevention aims to prevent disease before it occurs.", "Secondary prevention focuses on early detection and prompt treatment.", "Tertiary prevention reduces complications and supports function."], takeaway: "Vaccination is a common primary-prevention example; screening is secondary prevention." },
      { title: "Cold chain essentials", time: "4 min read", note: "The vaccine cold chain maintains recommended storage conditions from manufacture to administration.", points: ["Use approved temperature-monitoring equipment.", "Record and review temperatures as required.", "Follow local policy after a temperature excursion.", "Protect vaccines from heat, freezing and light as applicable."], takeaway: "Do not use potentially compromised stock until authorised guidance is obtained." },
      { title: "Breaking the chain of infection", time: "3 min read", note: "Infection prevention targets links in the chain of infection.", points: ["Infectious agent.", "Reservoir.", "Portal of exit.", "Mode of transmission.", "Portal of entry.", "Susceptible host."], takeaway: "Hand hygiene, vaccination, PPE and safe handling interrupt different links." }
    ]
  };
  const questions = [
    { q: "Which action is most effective for reducing transmission of many healthcare-associated pathogens?", options: ["Hand hygiene at the correct moments", "Wearing two pairs of gloves for every task", "Keeping every door closed", "Routine antibiotics for all patients"], answer: 0, why: "Correct hand hygiene at the appropriate moments is a core infection-prevention measure." },
    { q: "Which structure normally initiates the heartbeat's electrical impulse?", options: ["Atrioventricular node", "Sinoatrial node", "Bundle of His", "Purkinje fibres"], answer: 1, why: "The sinoatrial node normally acts as the heart's primary pacemaker." },
    { q: "In ADME, what does the letter M represent?", options: ["Movement", "Monitoring", "Metabolism", "Membrane"], answer: 2, why: "ADME stands for absorption, distribution, metabolism and excretion." },
    { q: "Which is an example of primary prevention?", options: ["Rehabilitation after a stroke", "Screening for hypertension", "Immunisation before exposure", "Managing an established complication"], answer: 2, why: "Primary prevention aims to prevent disease before it occurs; immunisation is a typical example." },
    { q: "Which nephron process returns needed substances from tubular fluid to blood?", options: ["Filtration", "Reabsorption", "Secretion", "Ventilation"], answer: 1, why: "Tubular reabsorption returns water and useful solutes to the bloodstream." },
    { q: "What should a nurse do when a medication order is unclear?", options: ["Guess from the usual dose", "Skip documentation", "Clarify the order with an authorised prescriber", "Ask another patient"], answer: 2, why: "Unclear orders should be clarified before administration; guessing creates avoidable risk." },
    { q: "Which vital sign describes pressure exerted by blood against arterial walls?", options: ["Temperature", "Blood pressure", "Respiratory rate", "Oxygen saturation"], answer: 1, why: "Blood pressure measures arterial pressure and should be interpreted with the patient's clinical context." },
    { q: "Which link in the chain of infection is targeted by respiratory source control?", options: ["Portal of exit", "Susceptible host only", "Reservoir only", "Portal of entry only"], answer: 0, why: "Source control can reduce infectious particles leaving an infected person's respiratory tract." },
    { q: "What does pulse oximetry estimate?", options: ["Blood glucose", "Haemoglobin oxygen saturation", "Cardiac output directly", "Blood pressure"], answer: 1, why: "Pulse oximetry estimates peripheral oxygen saturation; it does not directly measure cardiac output." },
    { q: "Which action is appropriate after noticing a potentially serious adverse drug reaction?", options: ["Ignore it if it is uncommon", "Document it next week", "Promptly assess, escalate and report per protocol", "Recommend a new dose independently"], answer: 2, why: "Patient safety comes first: obtain prompt clinical assessment, escalate and report according to local policy." }
  ];
  const state = loadState();
  let activeCourse = "bsc";
  let activeQuiz = null;
  let timerHandle = null;
  let timerRemaining = 25 * 60;
  let timerRunning = false;
  let timerKind = "focus";
  let quoteIndex = Math.floor(Math.random() * quotes.length);
  const $ = id => document.getElementById(id);
  const safeText = value => String(value ?? "");

  function freshState() {
    return { xp: 0, sessions: 0, attempts: 0, correct: 0, studied: [], activity: {}, lastStudyDate: "", completedTests: 0 };
  }
  function loadState() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
      if (!parsed || typeof parsed !== "object") return freshState();
      return { ...freshState(), ...parsed, studied: Array.isArray(parsed.studied) ? parsed.studied : [], activity: parsed.activity && typeof parsed.activity === "object" ? parsed.activity : {} };
    } catch (_) { return freshState(); }
  }
  function saveState() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (_) { toast("Browser storage is unavailable; progress may not persist."); }
    renderStats();
  }
  function localDateKey(date = new Date()) {
    return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");
  }
  function markActivity() {
    const key = localDateKey();
    state.activity[key] = true;
    state.lastStudyDate = key;
  }
  function toast(message) {
    const el = $("toast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toast._handle);
    toast._handle = setTimeout(() => el.classList.remove("show"), 2300);
  }
  function haptic() { try { tg?.HapticFeedback?.impactOccurred("light"); } catch (_) {} }
  function renderStats() {
    $("xp-stat").textContent = state.xp;
    $("sessions-stat").textContent = state.sessions;
    $("accuracy-stat").textContent = state.attempts ? Math.round(state.correct / state.attempts * 100) + "%" : "—";
    $("profile-xp").textContent = state.xp;
    $("profile-sessions").textContent = state.sessions;
    $("profile-answered").textContent = state.attempts;
    const accuracy = state.attempts ? Math.round(state.correct / state.attempts * 100) : 0;
    $("profile-accuracy").textContent = state.attempts ? accuracy + "%" : "—";
    $("accuracy-bar").style.width = accuracy + "%";
    renderWeek();
  }
  function renderWeek() {
    const labels = ["S", "M", "T", "W", "T", "F", "S"];
    const today = new Date();
    const mondayOffset = (today.getDay() + 6) % 7;
    const monday = new Date(today);
    monday.setDate(today.getDate() - mondayOffset);
    const box = $("week-panel");
    box.replaceChildren();
    for (let i = 0; i < 7; i++) {
      const day = new Date(monday);
      day.setDate(monday.getDate() + i);
      const key = localDateKey(day);
      const wrap = document.createElement("div");
      wrap.className = "week-day";
      const label = document.createElement("span");
      label.textContent = labels[(i + 1) % 7];
      const dot = document.createElement("div");
      dot.className = "week-dot" + (state.activity[key] ? " done" : "");
      dot.textContent = state.activity[key] ? "✓" : String(day.getDate());
      wrap.append(label, dot);
      box.append(wrap);
    }
  }
  function setView(name) {
    document.querySelectorAll(".view").forEach(v => v.classList.toggle("active", v.dataset.view === name));
    document.querySelectorAll(".nav").forEach(n => n.classList.toggle("active", n.dataset.tab === name || (name === "focus" && n.dataset.tab === "home")));
    if (name === "learn") renderTopics();
    if (name === "profile") renderProfileName();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function renderProfileName() {
    const user = tg?.initDataUnsafe?.user;
    const name = user?.first_name || "Student";
    $("profile-name").textContent = name;
    $("hello").textContent = "Ready to lock in, " + name + "?";
    $("avatar").textContent = user?.is_premium ? "💎" : "🧠";
    $("profile-avatar").textContent = user?.is_premium ? "💎" : "🧠";
  }
  function renderTopics() {
    const subject = $("subject-select").value;
    const items = lessons[subject] || [];
    const list = $("topic-list");
    list.replaceChildren();
    items.forEach((lesson, i) => {
      const button = document.createElement("button");
      button.className = "topic-button" + (i === 0 ? " active" : "");
      button.innerHTML = '<span class="topic-number">' + String(i + 1).padStart(2, "0") + '</span><span><strong></strong><small></small></span><span class="topic-chevron">↗</span>';
      button.querySelector("strong").textContent = lesson.title;
      button.querySelector("small").textContent = lesson.time + (state.studied.includes(subject + ":" + i) ? " · Completed ✓" : "");
      button.addEventListener("click", () => {
        list.querySelectorAll(".topic-button").forEach(b => b.classList.remove("active"));
        button.classList.add("active");
        renderLesson(subject, i);
      });
      list.append(button);
    });
    if (items.length) renderLesson(subject, 0);
  }
  function renderLesson(subject, index) {
    const lesson = lessons[subject][index];
    const key = subject + ":" + index;
    const panel = $("lesson-panel");
    panel.replaceChildren();
    const kicker = document.createElement("p");
    kicker.className = "note-kicker";
    kicker.textContent = activeCourse === "bsc" ? "B.SC NURSING • STUDY NOTE" : "GNM NURSING • STUDY NOTE";
    const title = document.createElement("h3");
    title.textContent = lesson.title;
    const intro = document.createElement("p");
    intro.textContent = lesson.note;
    const ul = document.createElement("ul");
    lesson.points.forEach(point => { const li = document.createElement("li"); li.textContent = point; ul.append(li); });
    const takeaway = document.createElement("p");
    takeaway.style.marginTop = "13px";
    takeaway.textContent = "Key takeaway: " + lesson.takeaway;
    const done = document.createElement("button");
    done.className = "button " + (state.studied.includes(key) ? "button-secondary" : "button-primary");
    done.style.marginTop = "15px";
    done.textContent = state.studied.includes(key) ? "✓ Topic completed" : "Mark topic complete · +2 XP";
    done.disabled = state.studied.includes(key);
    done.addEventListener("click", () => {
      if (state.studied.includes(key)) return;
      state.studied.push(key); state.xp += 2; markActivity(); saveState(); renderTopics(); renderLesson(subject, index);
      toast("Topic completed · +2 local XP");
    });
    panel.append(kicker, title, intro, ul, takeaway, done);
  }
  function startQuiz(kind) {
    finishQuizIfActive();
    timerKind = kind;
    const shuffled = questions.slice().sort(() => Math.random() - 0.5);
    activeQuiz = { kind, questions: shuffled.slice(0, 5), index: 0, correct: 0, answered: false, ended: false };
    const card = $(kind === "test" ? "test-card" : "quiz-card");
    if (kind === "test") {
      timerRemaining = 5 * 60;
      startCountdown("test");
    }
    renderQuestion(card);
    haptic();
  }
  function finishQuizIfActive() {
    if (activeQuiz && !activeQuiz.ended) activeQuiz.ended = true;
    if (timerKind === "test") stopCountdown();
  }
  function renderQuestion(card) {
    const quiz = activeQuiz;
    if (!quiz) return;
    card.replaceChildren();
    if (quiz.index >= quiz.questions.length) { renderQuizResult(card, false); return; }
    const item = quiz.questions[quiz.index];
    const meta = document.createElement("div");
    meta.className = "quiz-meta";
    const count = document.createElement("span");
    count.textContent = "QUESTION " + (quiz.index + 1) + " OF " + quiz.questions.length;
    const score = document.createElement("span");
    score.textContent = quiz.kind === "test" ? "⏱ " + formatTime(timerRemaining) + " · Score " + quiz.correct : "Score " + quiz.correct;
    meta.append(count, score);
    const question = document.createElement("h3");
    question.className = "quiz-question";
    question.textContent = item.q;
    const options = document.createElement("div");
    options.className = "answer-list";
    const letters = ["A", "B", "C", "D"];
    item.options.forEach((option, i) => {
      const button = document.createElement("button");
      button.className = "answer-option";
      button.innerHTML = '<span class="option-letter">' + letters[i] + '</span><span></span>';
      button.lastElementChild.textContent = option;
      button.addEventListener("click", () => submitAnswer(i, card));
      options.append(button);
    });
    card.append(meta, question, options);
  }
  function submitAnswer(choice, card) {
    const quiz = activeQuiz;
    if (!quiz || quiz.answered || quiz.ended) return;
    const item = quiz.questions[quiz.index];
    quiz.answered = true;
    const correct = choice === item.answer;
    state.attempts += 1;
    if (correct) { state.correct += 1; quiz.correct += 1; state.xp += 1; }
    markActivity(); saveState();
    const buttons = card.querySelectorAll(".answer-option");
    buttons.forEach((button, i) => {
      button.disabled = true;
      if (i === item.answer) button.classList.add("correct");
      if (i === choice && !correct) button.classList.add("incorrect");
    });
    const feedback = document.createElement("div");
    feedback.className = "answer-feedback";
    const heading = document.createElement("strong");
    heading.textContent = correct ? "✓ Correct · +1 local XP" : "Not quite — review the concept";
    const body = document.createElement("span");
    body.textContent = item.why;
    feedback.append(heading, body);
    const footer = document.createElement("div");
    footer.className = "quiz-footer";
    const note = document.createElement("small");
    note.textContent = "Your progress is saved on this device.";
    const next = document.createElement("button");
    next.className = "button button-primary";
    next.textContent = quiz.index === quiz.questions.length - 1 ? "See results →" : "Next question →";
    next.addEventListener("click", () => {
      if (!activeQuiz || activeQuiz !== quiz) return;
      quiz.index += 1; quiz.answered = false;
      renderQuestion(card);
    });
    footer.append(note, next);
    card.append(feedback, footer);
    haptic();
  }
  function renderQuizResult(card, timedOut) {
    const quiz = activeQuiz;
    if (!quiz) return;
    quiz.ended = true;
    if (quiz.kind === "test") { stopCountdown(); state.completedTests += 1; }
    const result = document.createElement("div");
    result.className = "empty-state";
    const icon = document.createElement("span");
    icon.textContent = quiz.correct >= 4 ? "🏆" : quiz.correct >= 3 ? "✨" : "🧠";
    const title = document.createElement("strong");
    title.textContent = timedOut ? "Time's up — review your result" : "Run complete";
    const text = document.createElement("p");
    text.textContent = "You got " + quiz.correct + " out of " + quiz.questions.length + " correct (" + Math.round(quiz.correct / quiz.questions.length * 100) + "%). " + (quiz.correct >= 4 ? "Strong work. Keep revising." : "Review the explanations and try again.");
    const restart = document.createElement("button");
    restart.className = "button button-primary";
    restart.textContent = "Try another set ↻";
    restart.addEventListener("click", () => startQuiz(quiz.kind));
    result.append(icon, title, text, restart);
    card.replaceChildren(result);
    if (quiz.kind === "test") saveState();
  }
  function startCountdown(kind) {
    stopCountdown();
    timerKind = kind;
    timerHandle = setInterval(() => {
      if (kind === "focus" && !timerRunning) return;
      timerRemaining = Math.max(0, timerRemaining - 1);
      if (kind === "focus") updateTimerDisplay();
      else if (activeQuiz && !activeQuiz.ended) {
        const score = $("test-card").querySelector(".quiz-meta span:last-child");
        if (score) score.textContent = "⏱ " + formatTime(timerRemaining) + " · Score " + activeQuiz.correct;
      }
      if (timerRemaining <= 0) {
        stopCountdown();
        if (kind === "focus") completeFocusSession();
        else if (activeQuiz && !activeQuiz.ended) renderQuizResult($("test-card"), true);
      }
    }, 1000);
  }
  function stopCountdown() { if (timerHandle) clearInterval(timerHandle); timerHandle = null; }
  function formatTime(seconds) { return String(Math.floor(seconds / 60)).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0"); }
  function updateTimerDisplay() {
    $("timer-display").textContent = formatTime(timerRemaining);
    $("timer-status").textContent = timerRunning ? "FOCUS IN PROGRESS" : timerRemaining === 25 * 60 ? "READY TO FOCUS" : "PAUSED";
    $("timer-ring").style.setProperty("--timer-progress", ((25 * 60 - timerRemaining) / (25 * 60) * 100) + "%");
    $("timer-start").textContent = timerRunning ? "Pause timer" : "Resume timer";
  }
  function startFocus() {
    setView("focus");
    if (!timerRunning && timerRemaining === 25 * 60) $("focus-goal").focus({ preventScroll: true });
  }
  function toggleFocusTimer() {
    if (timerRemaining <= 0) timerRemaining = 25 * 60;
    timerRunning = !timerRunning;
    if (timerRunning) {
      if (!timerHandle) startCountdown("focus");
      $("timer-start").textContent = "Pause timer";
      toast("Focus mode on. One task at a time.");
    } else {
      stopCountdown();
      $("timer-start").textContent = "Resume timer";
    }
    updateTimerDisplay();
  }
  function completeFocusSession() {
    timerRunning = false; timerRemaining = 0;
    $("timer-display").textContent = "00:00";
    $("timer-status").textContent = "SESSION COMPLETE";
    $("timer-start").textContent = "Start another";
    state.sessions += 1; state.xp += 5; markActivity(); saveState();
    $("focus-hint").textContent = "Completed: " + ($("focus-goal").value.trim() || "Focused study") + ". Nice work — +5 local XP.";
    toast("Focus session complete · +5 local XP");
    try { tg?.HapticFeedback?.notificationOccurred("success"); } catch (_) {}
  }
  function resetTimer() {
    stopCountdown(); timerRunning = false; timerRemaining = 25 * 60;
    updateTimerDisplay(); $("timer-start").textContent = "Start timer";
    $("focus-hint").textContent = "Complete the timer to record a session and earn 5 local XP.";
  }
  function shareApp() {
    const url = window.location.href.split("#")[0];
    const text = "Study with me on Bhushan Science — focus, learn and practise nursing concepts.";
    const shareUrl = "https://t.me/share/url?url=" + encodeURIComponent(url) + "&text=" + encodeURIComponent(text);
    try { if (tg?.openTelegramLink) tg.openTelegramLink(shareUrl); else window.open(shareUrl, "_blank", "noopener,noreferrer"); }
    catch (_) { toast("Open Telegram's share menu to invite a study partner."); }
  }
  function showHelp() {
    const message = "For bot support, return to the Bhushan Science Bot chat and use /help. This Mini App's study stats are stored locally and are not synced to the bot yet.";
    if (tg?.showPopup) tg.showPopup({ title: "Need help?", message, buttons: [{ type: "ok", text: "Got it" }] });
    else toast(message);
  }
  function action(name) {
    haptic();
    if (name === "focus") return startFocus();
    if (name === "learn") return setView("learn");
    if (name === "practice") return setView("practice");
    if (name === "practice-start") return startQuiz("practice");
    if (name === "test") return setView("test");
    if (name === "test-start") return startQuiz("test");
    if (name === "refer") return shareApp();
    if (name === "help") return showHelp();
    if (name === "refresh") {
      quoteIndex = (quoteIndex + 1) % quotes.length;
      $("quote-text").textContent = quotes[quoteIndex];
      toast("Your daily reminder has been refreshed.");
      return;
    }
    if (name === "reset-progress") {
      const reset = () => {
        Object.assign(state, freshState());
        saveState(); renderTopics();
        toast("Local progress reset.");
      };
      if (tg?.showPopup) tg.showPopup({ title: "Reset local progress?", message: "This clears the XP, practice history and completed topics stored on this device.", buttons: [{ id: "cancel", type: "cancel" }, { id: "reset", type: "destructive", text: "Reset" }] }, buttonId => { if (buttonId === "reset") reset(); });
      else if (window.confirm("Reset all local study progress on this device?")) reset();
      return;
    }
  }

  document.querySelectorAll("[data-tab]").forEach(button => button.addEventListener("click", () => setView(button.dataset.tab)));
  document.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => action(button.dataset.action)));
  $("profile-shortcut").addEventListener("click", () => setView("profile"));
  document.querySelectorAll("[data-course]").forEach(button => button.addEventListener("click", () => {
    activeCourse = button.dataset.course;
    document.querySelectorAll("[data-course]").forEach(b => b.classList.toggle("active", b === button));
    renderTopics();
  }));
  $("subject-select").addEventListener("change", renderTopics);
  $("new-quote").addEventListener("click", () => {
    quoteIndex = (quoteIndex + 1) % quotes.length;
    $("quote-text").textContent = quotes[quoteIndex];
  });
  $("timer-start").addEventListener("click", () => {
    if (timerRemaining === 0) resetTimer();
    toggleFocusTimer();
  });
  $("timer-reset").addEventListener("click", resetTimer);

  $("today-label").textContent = new Intl.DateTimeFormat("en", { weekday: "long", month: "short", day: "numeric" }).format(new Date()).toUpperCase();
  renderProfileName();
  renderStats();
  renderTopics();
  $("quote-text").textContent = quotes[quoteIndex];
  updateTimerDisplay();
  $("timer-start").textContent = "Start timer";
  if (tg?.initDataUnsafe?.user) {
    const firstName = tg.initDataUnsafe.user.first_name || "Student";
    $("hello").textContent = "Ready to lock in, " + firstName + "?";
  }
})();