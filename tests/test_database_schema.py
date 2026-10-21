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

    def test_soft_deleted_rows_are_retained(self):
        bot.init_db()
        with sqlite3.connect(bot.DB_FILE) as conn:
            conn.execute(
                "INSERT INTO quotes(text, author, is_active) VALUES(?, ?, 1)",
                ("Keep this row", "test"),
            )
            conn.commit()
            conn.execute(
                "UPDATE quotes SET is_active=0 WHERE text=?",
                ("Keep this row",),
            )
            conn.commit()
            row = conn.execute(
                "SELECT text, is_active FROM quotes WHERE text=?",
                ("Keep this row",),
            ).fetchone()
        self.assertEqual(row, ("Keep this row", 0))

    def test_source_has_no_hard_delete_or_replace_statements(self):
        source_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot.py")
        with open(source_path, encoding="utf-8") as source_file:
            source = source_file.read().upper()
        self.assertNotIn("DELETE FROM", source)
        self.assertNotIn("INSERT OR REPLACE", source)

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
