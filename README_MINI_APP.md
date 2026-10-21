# Bhushan Science Mini App

The `webapp/` folder contains the English-language, dark-theme Telegram Mini App.

## Included in this version

- Responsive dark dashboard designed for Telegram mobile and desktop.
- Learn library with short original study notes for Nursing Fundamentals, Anatomy & Physiology, Pharmacology, and Community Health.
- B.Sc Nursing and GNM course selectors.
- Original practice questions with instant correctness feedback and explanations.
- Five-question mini mock with a five-minute timer.
- 25-minute focus timer with pause/reset and completion tracking.
- Local XP, topic completion, quiz accuracy, focus sessions, and weekly activity.
- Telegram share flow and accessible navigation.
- Regression checks for markup, required controls, asset paths, and accidental frontend secrets.

## Progress and security boundaries

Study progress is currently saved in the browser's `localStorage` on that device. It is **not synced** with the Telegram bot, SQLite database, or a server. Local XP is motivational UI state, not an account balance or reward in the bot.

AI doubt solving, authenticated user analytics, cross-device progress, server-backed referrals, and server-authoritative scores require backend endpoints and server-side Telegram `initData` validation. They are not represented as connected features in this frontend-only release. The frontend must never contain `BOT_TOKEN`, webhook secrets, or provider credentials.

## Deploy

1. Enable GitHub Pages with **Source: GitHub Actions**.
2. The `.github/workflows/deploy-miniapp.yml` workflow deploys the `webapp/` folder from `main`.
3. Set the Render environment variable `WEBAPP_URL` to the deployed Pages URL:
   `https://bhushanscience.github.io/bhushan-science-bot/`
4. Redeploy the Render service after merging changes to `main`.

Render's Telegram bot remains a separate service from the static Mini App. A successful Pages deployment alone does not confirm that Telegram polling, the bot token, or the Render service is healthy.
