"""Versioned, self-hosted content update API for the Bhushan Science app.

No Firebase or Supabase. The update store is SQLite and can be placed on a
Render persistent disk with UPDATE_DB_PATH=/var/data/bhushan_updates.db.
"""
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, make_response, request

update_api = Blueprint("update_api", __name__, url_prefix="/api/v1")
DEFAULT_DB = os.environ.get("UPDATE_DB_PATH", "bhushan_science.db")
MAX_PAYLOAD_BYTES = 1024 * 1024


def _connect():
    conn = sqlite3.connect(DEFAULT_DB, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS app_update_releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL UNIQUE,
            payload_json TEXT NOT NULL,
            release_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )"""
    )
    return conn


def _manifest(row):
    if row is None:
        return {
            "version": 0,
            "release_notes": "",
            "updated_at": None,
            "payload": {},
        }
    return {
        "version": int(row["version"]),
        "release_notes": row["release_notes"],
        "updated_at": row["created_at"],
        "payload": json.loads(row["payload_json"]),
    }


def _admin_authorized():
    configured = os.environ.get("BHUSHAN_UPDATE_ADMIN_KEY", "")
    supplied = request.headers.get("X-Admin-Key", "")
    return bool(configured) and bool(supplied) and hmac.compare_digest(
        configured.encode("utf-8"), supplied.encode("utf-8")
    )


@update_api.get("/updates/manifest")
def get_update_manifest():
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT version, payload_json, release_notes, created_at "
            "FROM app_update_releases ORDER BY version DESC LIMIT 1"
        ).fetchone()
        response = make_response(jsonify(_manifest(row)))
        response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        conn.close()


@update_api.get("/updates/health")
def update_health():
    return jsonify({"ok": True, "service": "bhushan-content-updates"})


@update_api.post("/admin/auth/check")
def check_admin_credentials():
    if not _admin_authorized():
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    return jsonify({"ok": True, "role": "admin"})


@update_api.post("/admin/updates")
def publish_update():
    if not _admin_authorized():
        # Do not reveal whether the key is missing or incorrect.
        return jsonify({"error": "unauthorized"}), 401

    if request.content_length and request.content_length > MAX_PAYLOAD_BYTES:
        return jsonify({"error": "payload_too_large", "max_bytes": MAX_PAYLOAD_BYTES}), 413

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "expected_json_object"}), 400

    payload = body.get("payload", {})
    release_notes = body.get("release_notes", "")
    if not isinstance(payload, dict):
        return jsonify({"error": "payload_must_be_object"}), 400
    if not isinstance(release_notes, str):
        return jsonify({"error": "release_notes_must_be_text"}), 400

    try:
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_payload"}), 400
    if len(payload_json.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        return jsonify({"error": "payload_too_large", "max_bytes": MAX_PAYLOAD_BYTES}), 413

    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute(
            "SELECT COALESCE(MAX(version), 0) AS version FROM app_update_releases"
        ).fetchone()["version"]
        version = int(current) + 1
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO app_update_releases(version,payload_json,release_notes,created_at) "
            "VALUES(?,?,?,?)",
            (version, payload_json, release_notes[:500], created_at),
        )
        conn.commit()
        return jsonify({
            "ok": True,
            "version": version,
            "updated_at": created_at,
            "message": "Update published. App clients will receive it on their next sync.",
        }), 201
    except Exception:
        conn.rollback()
        current_app.logger.exception("Failed to publish Bhushan Science update")
        return jsonify({"error": "publish_failed"}), 500
    finally:
        conn.close()
