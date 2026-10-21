"""Smoke tests for additive SQLite schema migrations."""
import os
import sqlite3
import tempfile
import unittest

import bot


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous_db = bot.DB_FILE
        bot.DB_FILE = os.path.join(self.tmp.name, "test.sqlite3")

    def tearDown(self):
        bot.DB_FILE = self.previous_db
        self.tmp.cleanup()

    def test_security_and_support_tables_are_created_additively(self):
        bot.init_db()
        with sqlite3.connect(bot.DB_FILE) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertTrue(
                {"force_channels", "support_tickets", "admin_audit", "event_tickets"}
                .issubset(tables)
            )

    def test_ticket_checkin_is_single_use(self):
        bot.init_db()
        with sqlite3.connect(bot.DB_FILE) as conn:
            conn.execute(
                "INSERT INTO event_tickets(code, attendee_name, details) VALUES(?, ?, ?)",
                ("TEST-001", "Example attendee", "Test ticket"),
            )
            conn.commit()
            first = conn.execute(
                "UPDATE event_tickets SET is_checked_in=1 WHERE code=? AND is_checked_in=0 "
                "RETURNING code",
                ("TEST-001",),
            ).fetchone()
            second = conn.execute(
                "UPDATE event_tickets SET is_checked_in=1 WHERE code=? AND is_checked_in=0 "
                "RETURNING code",
                ("TEST-001",),
            ).fetchone()
        self.assertEqual(first[0], "TEST-001")
        self.assertIsNone(second)

    def test_reinitialization_preserves_ticket_rows(self):
        bot.init_db()
        with sqlite3.connect(bot.DB_FILE) as conn:
            conn.execute(
                "INSERT INTO event_tickets(code, attendee_name) VALUES(?, ?)",
                ("KEEP-001", "Preserved attendee"),
            )
            conn.commit()
        bot.init_db()
        with sqlite3.connect(bot.DB_FILE) as conn:
            row = conn.execute(
                "SELECT attendee_name FROM event_tickets WHERE code=?",
                ("KEEP-001",),
            ).fetchone()
        self.assertEqual(row[0], "Preserved attendee")


if __name__ == "__main__":
    unittest.main()
