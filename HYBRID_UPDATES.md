# Bhushan Science hybrid content updates

This update service uses the existing Flask service and SQLite. It does not use
Firebase or Supabase.

## Render configuration

On the Render service that runs `python bot.py`, set:

- `BHUSHAN_UPDATE_ADMIN_KEY`: a long, random secret (at least 32 random bytes).
- `UPDATE_DB_PATH`: `/var/data/bhushan_updates.db`.

Attach a Render persistent disk mounted at `/var/data`. Without persistent
storage, the update history may be lost when the service is replaced or
redeployed. Keep the admin key private; do not commit it to GitHub or put it in
source code.

The existing health endpoints remain:
- `/`
- `/health`

New endpoints:
- `GET /api/v1/updates/health`
- `GET /api/v1/updates/manifest` (public read-only manifest)
- `POST /api/v1/admin/updates` (requires `X-Admin-Key`)

## Android app

The Flutter app checks the manifest on startup and caches the last successful
manifest using SharedPreferences. If the phone is offline, the app keeps using
the cached manifest. The Admin tab includes **Remote content updates**:
1. Check the latest server version.
2. Enter the server-side admin key (it is held only in the screen's memory).
3. Add release notes and a JSON payload.
4. Publish. All installed app versions that sync against this server can read
   the new manifest on their next successful sync.

Example payload:

```json
{
  "announcement": "The next nursing revision set is now available."
}
```

The first client integration displays the remote `announcement` on Home and
caches the full payload locally. Further app content sections (semester
subjects, lesson bodies, quiz banks, and study-technique presets) must read
their corresponding keys from this cached payload before those items can be
managed entirely from the Admin screen.

## Important boundary

This is a **content/configuration update channel**, not an APK updater. It can
publish data and announcements to existing installations. New native Flutter
features, permissions, or UI code still require a newly built APK and normal
Android installation/update flow.
