from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEBAPP = ROOT / "webapp"


class AppMarkupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.assets = []
        self.elements = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet" and attrs.get("href"):
            self.assets.append(attrs["href"])
        self.elements.append(tag)


class MiniAppRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEBAPP / "index.html").read_text(encoding="utf-8")
        cls.js = (WEBAPP / "app.js").read_text(encoding="utf-8")
        cls.css = (WEBAPP / "style.css").read_text(encoding="utf-8")
        cls.parser = AppMarkupParser()
        cls.parser.feed(cls.html)

    def test_markup_has_required_views_and_controls(self):
        required = {
            "view-home", "view-learn", "view-practice", "view-test", "view-focus",
            "view-profile", "topic-list", "lesson-panel", "quiz-card", "test-card",
            "timer-display", "timer-start", "timer-reset", "week-panel", "toast",
        }
        self.assertTrue(required.issubset(self.parser.ids), required - self.parser.ids)

    def test_frontend_assets_exist(self):
        for asset in self.parser.assets:
            if asset.startswith(("http://", "https://")):
                continue
            self.assertTrue((WEBAPP / asset).is_file(), f"Missing frontend asset: {asset}")

    def test_required_interactions_are_wired(self):
        for marker in ("startQuiz", "submitAnswer", "renderLesson", "completeFocusSession",
                       "renderStats", "shareApp", "reset-progress"):
            self.assertIn(marker, self.js)
        self.assertIn("localStorage", self.js)
        self.assertIn("data-tab", self.html)
        self.assertIn(".bottom-nav", self.css)

    def test_no_telegram_token_or_secret_in_frontend(self):
        combined = self.html + "\n" + self.js + "\n" + self.css
        self.assertNotRegex(combined, re.compile(r"\b\d{7,}:[A-Za-z0-9_-]{25,}\b"))
        self.assertNotIn("BOT_TOKEN", combined)
        self.assertNotIn("WEBHOOK_SECRET", combined)

    def test_accessibility_and_reduced_motion_basics(self):
        self.assertIn('aria-label="Main navigation"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn("prefers-reduced-motion", self.css)


if __name__ == "__main__":
    unittest.main()
