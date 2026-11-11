import json
import os
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask
import update_api


class HybridUpdateApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "updates.db")
        self.db_patch = patch.object(update_api, "DEFAULT_DB", self.db_path)
        self.db_patch.start()
        self.app = Flask(__name__)
        self.app.register_blueprint(update_api.update_api)
        self.client = self.app.test_client()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_manifest_starts_empty(self):
        response = self.client.get("/api/v1/updates/manifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["version"], 0)
        self.assertEqual(response.get_json()["payload"], {})

    def test_publish_requires_admin_key(self):
        with patch.dict(os.environ, {"BHUSHAN_UPDATE_ADMIN_KEY": "test-secret"}):
            response = self.client.post(
                "/api/v1/admin/updates",
                json={"payload": {"announcement": "Hello"}},
            )
        self.assertEqual(response.status_code, 401)

    def test_admin_auth_check_rejects_invalid_credentials(self):
        with patch.dict(os.environ, {"BHUSHAN_UPDATE_ADMIN_KEY": "test-secret"}):
            response = self.client.post(
                "/api/v1/admin/auth/check",
                headers={"X-Admin-Key": "wrong"},
                json={},
            )
        self.assertEqual(response.status_code, 401)

    def test_admin_auth_check_accepts_valid_credentials(self):
        with patch.dict(os.environ, {"BHUSHAN_UPDATE_ADMIN_KEY": "test-secret"}):
            response = self.client.post(
                "/api/v1/admin/auth/check",
                headers={"X-Admin-Key": "test-secret"},
                json={},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def test_publish_then_fetch_manifest(self):
        with patch.dict(os.environ, {"BHUSHAN_UPDATE_ADMIN_KEY": "test-secret"}):
            response = self.client.post(
                "/api/v1/admin/updates",
                headers={"X-Admin-Key": "test-secret"},
                json={
                    "release_notes": "Added a new topic",
                    "payload": {"announcement": "New lesson available", "subjects": ["Anatomy"]},
                },
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["version"], 1)

        manifest = self.client.get("/api/v1/updates/manifest")
        self.assertEqual(manifest.status_code, 200)
        data = manifest.get_json()
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["release_notes"], "Added a new topic")
        self.assertEqual(data["payload"]["announcement"], "New lesson available")

    def test_invalid_payload_is_rejected(self):
        with patch.dict(os.environ, {"BHUSHAN_UPDATE_ADMIN_KEY": "test-secret"}):
            response = self.client.post(
                "/api/v1/admin/updates",
                headers={"X-Admin-Key": "test-secret"},
                json={"payload": ["not", "an", "object"]},
            )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
