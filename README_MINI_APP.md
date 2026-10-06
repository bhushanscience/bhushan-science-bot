# Bhushan Science Mini App 🚀

The `webapp/` folder contains the Telegram Mini App frontend.

Set Render environment variable:
`WEBAPP_URL=https://bhushanscience.github.io/bhushan-science-bot/`

Enable GitHub Pages with **Source: GitHub Actions**. The included workflow deploys `webapp/`.

The first release includes a premium mobile dashboard, Learn/Practice/Test cards, NORCET roadmap, progress analytics, AI Doubt Lab entry point, Refer & Earn entry point, emoji/sticker-style UI and a motivation GIF.

Before exposing private user scores/points from the database, add server-side validation of Telegram `initData` and authenticated API endpoints.
