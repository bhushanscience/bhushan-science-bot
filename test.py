"""
FarmRise Auto Scratch + Redeem v4.3
✅ FIXED 1 Device + 1 Location only (OnePlus 8T @ Hyderabad)
✅ Login ke baad 2 baar Track
✅ UPI sirf scratch ke baad
✅ OTP fast retry + (r)/(c)
✅ Claim In Process = Work Done
✅ Full Live Debug har API pe
"""
import requests, json, time, uuid, os, sys, random
from datetime import datetime

# ============================================================
# COLORS
# ============================================================
class C:
    RESET="\033[0m"; BOLD="\033[1m"
    RED="\033[91m"; GREEN="\033[92m"; YELLOW="\033[93m"
    BLUE="\033[94m"; MAGENTA="\033[95m"; CYAN="\033[96m"
def ok(m):   return f"{C.GREEN}{C.BOLD}{m}{C.RESET}"
def err(m):  return f"{C.RED}{C.BOLD}{m}{C.RESET}"
def warn(m): return f"{C.YELLOW}{C.BOLD}{m}{C.RESET}"
def info(m): return f"{C.CYAN}{m}{C.RESET}"
def title(m):return f"{C.MAGENTA}{C.BOLD}{m}{C.RESET}"
def debug(m):return f"{C.BLUE}🔍 {m}{C.RESET}"

# ============================================================
# FIXED DEVICE + LOCATION (sirf yeh use hoga)
# ============================================================
FIXED_DEVICE = {
    "id": "f0e1d2c3b4a59687",
    "model": "OnePlus 8T",
    "brand": "OnePlus",
    "name": "OnePlus8T",
    "android": "11"
}
FIXED_LOCATION = {
    "lat": "17.3850440",
    "long": "78.4866710",
    "city": "Hyderabad",
    "state": "TELANGANA"
}

# ============================================================
# CONFIG
# ============================================================
BASE_NEW    = "https://api.new.farmrise.bayer.com"
BASE_PUBLIC = "https://api.public.farmrise.bayer.com"
TRACK_URL   = "https://plat.api.production.farmrise.com/track"
APP_VERSION = "2.72.6"
T_AND_C_ID  = "35"
LANG_ID     = "1"
LANG_ISO    = "en"
SESSION_FILE = "farmrise_session.json"
POLL_INTERVAL = 15

# ============================================================
# SESSION
# ============================================================
session = requests.Session()
state = {
    "acquired_user_id": None,
    "registered_user_id": None,
    "security_token": None,
    "refresh_token": None,
    "phone": None,
    "device": FIXED_DEVICE,
    "location": FIXED_LOCATION,
    "anonymous_id": None,
}

def save_session():
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({**state, "saved_at": datetime.now().isoformat()}, f, indent=2)
    print(ok("💾 Session saved"))

def load_session():
    if not os.path.exists(SESSION_FILE): return False
    try:
        data = json.load(open(SESSION_FILE, encoding="utf-8"))
        if not data.get("security_token"): return False
        state.update({k: data.get(k) for k in state})
        # Force fixed device + location even on load
        state["device"] = FIXED_DEVICE
        state["location"] = FIXED_LOCATION
        print(ok(f"📂 Loaded | {state['phone']}"))
        return True
    except: return False

def delete_session():
    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)

# ============================================================
# FULL LIVE DEBUG REQ
# ============================================================
def req(method, url, **kwargs):
    dev = state["device"]
    loc = state["location"]

    h = {**kwargs.pop("headers", {})}
    h["appversion"] = APP_VERSION
    h["countryisocode"] = "IN"
    h["languageid"] = LANG_ID
    h["languageiso"] = LANG_ISO
    h["user-agent"] = f"Dalvik/2.1.0 (Linux; U; Android {dev['android']}; {dev['model']})"
    h["accept-encoding"] = "gzip"
    h["cache-control"] = "no-cache"
    h["pragma"] = "no-cache"
    h["requestid"] = str(uuid.uuid4())
    h["deviceid"] = dev["id"]
    h["latitude"] = loc["lat"]
    h["longitude"] = loc["long"]
    h["state"] = loc["state"]
    h["role"] = "FARMER"

    if state.get("acquired_user_id"):
        h["acquireduserid"] = state["acquired_user_id"]
    if state.get("registered_user_id"):
        h["registereduserid"] = state["registered_user_id"]
    if state.get("security_token"):
        h["authorization"] = state["security_token"]

    # LIVE DEBUG - Request
    print(debug(f"→ {method} {url}"))
    print(info(f"   deviceid={dev['id']} | {dev['brand']} {dev['model']} @ {loc['city']}"))
    if state.get("security_token"):
        print(info(f"   auth=...{state['security_token'][-12:]}"))

    t0 = time.time()
    try:
        r = session.request(method, url, headers=h, timeout=20, **kwargs)
        ms = (time.time() - t0) * 1000

        # LIVE DEBUG - Response
        status_line = f"[{method:<6}] {url.replace('https://','')[:65]:<65} → {r.status_code} ({ms:.0f}ms)"
        if 200 <= r.status_code < 300:
            print(ok(status_line))
        elif 300 <= r.status_code < 400:
            print(warn(status_line))
        else:
            print(err(status_line))
            # Error body bhi dikhao
            try:
                body = r.text[:300] if r.text else ""
                if body:
                    print(err(f"   📄 {body}"))
            except: pass

        return r
    except Exception as e:
        print(err(f"[{method}] EXCEPTION → {e}"))
        return None

# ============================================================
# AUTH
# ============================================================
def acquire_user():
    print(title("\n=== Acquire user ==="))
    r = req("POST", f"{BASE_PUBLIC}/v1/acquired_users", json={
        "deviceId": FIXED_DEVICE["id"],
        "languageId": LANG_ID,
        "termsAndConditionsId": T_AND_C_ID,
        "userSourceBO": {"utmMedium": "organic", "utmSource": "google-play"},
    })
    if r and r.status_code in (200, 201):
        state["acquired_user_id"] = r.json()["data"]["acquiredUserId"]
        state["anonymous_id"] = str(uuid.uuid4())
        print(ok(f"✅ acquired = {state['acquired_user_id']}"))
        return True
    return False

def send_otp(phone):
    print(title(f"\n=== Send OTP → {phone} ==="))
    r = req("POST", f"{BASE_NEW}/v1/challenge",
            json={"phoneNumber": f"+91{phone}", "whatsappOTPConsent": True})
    if r and r.status_code == 200:
        print(ok(f"✅ {r.json().get('data', {}).get('message', 'OTP sent')}"))
        state["phone"] = phone
        return True
    print(err(f"❌ Send OTP failed"))
    return False

def verify_otp(otp, max_retries=15, fast_delay=0.7):
    print(title(f"\n=== Verify OTP → {otp} ==="))
    for attempt in range(1, max_retries + 1):
        r = req("POST", f"{BASE_NEW}/v1/verify_challenge",
                json={"otp": otp, "phoneNumber": state["phone"]})

        if r is None:
            print(warn(f"⚠️ Attempt {attempt}/{max_retries} → No response, retrying..."))
            time.sleep(fast_delay)
            continue

        if r.status_code in (200, 201):
            d = r.json()["data"]
            state["security_token"] = d.get("securityToken", "")
            state["refresh_token"] = d.get("refreshToken", "")
            state["registered_user_id"] = d.get("registeredUserId")
            if not state.get("anonymous_id"):
                state["anonymous_id"] = str(uuid.uuid4())
            print(ok("✅ Login successful"))
            print(debug(f"userId = {state['registered_user_id']}"))
            print(debug(f"token  = ...{state['security_token'][-18:]}"))
            save_session()
            return True

        if r.status_code in (500, 502, 503, 429, 408):
            print(warn(f"⚠️ Attempt {attempt}/{max_retries} → {r.status_code} — fast retry..."))
            time.sleep(fast_delay)
            continue

        print(err(f"❌ Permanent fail {r.status_code}"))
        return False

    print(err("❌ Max retries reached"))
    return False

def get_otp_with_retry(phone):
    while True:
        print(info("\n🔄 (r)=resend new OTP | Enter=re-enter OTP | (c)=cancel:"))
        choice = input(info("🔑 OTP / choice: ")).strip().lower()

        if choice == "c":
            print(warn("🚫 Cancelled"))
            return False
        if choice == "r":
            if not send_otp(phone):
                print(err("❌ Resend failed"))
                continue
            print(ok("✅ New OTP sent"))
            continue
        if choice == "":
            continue

        otp = choice
        if len(otp) != 6 or not otp.isdigit():
            print(err("❌ 6 digit OTP chahiye"))
            continue

        if verify_otp(otp):
            return True
        else:
            print(warn("⚠️ Fail. (r) resend / (c) cancel / ya naya OTP daalo"))

def validate_session():
    if not state.get("security_token"): return False
    r = req("GET", f"{BASE_NEW}/user_service/v2/registered_users/{state['registered_user_id']}")
    return r is not None and r.status_code == 200

# ============================================================
# TRACK
# ============================================================
def send_track(event, props):
    if not state.get("anonymous_id"):
        state["anonymous_id"] = str(uuid.uuid4())

    dev = state["device"]

    item = {
        "messageId": str(uuid.uuid4()),
        "type": "track",
        "channel": "mobile",
        "context": {
            "app": {
                "build": 297,
                "name": "FarmRise",
                "namespace": "com.climate.farmrise",
                "version": APP_VERSION
            },
            "library": {
                "name": "analytics-android",
                "versionName": "1.0",
                "version": 1
            },
            "traits": {"anonymousId": state["anonymous_id"]},
            "os": {
                "name": "REL",
                "sdk": 32,
                "version": dev["android"]
            },
            "timezone": "Asia/Calcutta",
            "device": {
                "name": dev["name"],
                "model": dev["model"],
                "id": dev["id"],
                "brand": dev["brand"],
                "manufacturer": dev["brand"]
            },
            "network": {
                "wifi": True,
                "carrier": "",
                "bluetooth": False,
                "cellular": False
            },
        },
        "anonymousId": state["anonymous_id"],
        "originalTimestamp": datetime.now().astimezone().isoformat(),
        "integrations": {"All": True},
        "event": event,
        "properties": props,
    }

    if state.get("registered_user_id"):
        item["userId"] = state["registered_user_id"]
        item["context"]["traits"]["userId"] = state["registered_user_id"]

    r = req("POST", TRACK_URL, json=[item])
    return r is not None and r.status_code == 200

def do_track_twice():
    print(title("\n=== Track (2 times) ==="))
    props = {
        "user_declaration_status": 0,
        "coin_balance": 0,
        "screen_name": "coins_main",
        "utm_campaign": "q3_shf_non_commercial_reach",
        "flp_availability": "yes",
        "utm_medium": "whatsapp",
        "countryISOCode": "IN",
        "burn_availability": "yes",
        "source_name": "deep_link",
        "utm_source": "utm_instant_reward_shf_reach",
    }
    for i in range(1, 3):
        print(info(f"→ Track #{i}"))
        if send_track("app.farmrise.bayer_coins_main.screen.entered", props):
            print(ok(f"✅ Track #{i} success"))
        else:
            print(warn(f"⚠️ Track #{i} failed"))
        time.sleep(1.5)

# ============================================================
# DATA
# ============================================================
def get_balance():
    r = req("GET", f"{BASE_NEW}/farmer_reward_service/v1/user/{state['registered_user_id']}/balance-point")
    if r and r.status_code == 200:
        return r.json().get("data", {}).get("balancePoint", 0)
    return None

def get_profile():
    r = req("GET", f"{BASE_NEW}/user_service/v2/registered_users/{state['registered_user_id']}")
    if r and r.status_code == 200:
        d = r.json().get("data", {})
        print(ok(f"👤 {d.get('phoneNumber')} | {d.get('location')}"))
        return d
    return None

def get_unclaimed():
    r = req("GET", f"{BASE_NEW}/farmer_reward_service/v2/user/{state['registered_user_id']}/rewards/unclaimed")
    if r and r.status_code == 200:
        return r.json().get("data", [])
    return []

# ============================================================
# SCRATCH + CLAIM
# ============================================================
def scratch_card(reward_id):
    r = req("POST", f"{BASE_NEW}/farmer_reward_service/v1/user/scratchcard/scratched",
            json={"registeredUserId": state["registered_user_id"], "rewardId": reward_id})
    if r and r.status_code == 200:
        return r.json().get("data", {})
    return None

def validate_upi(upi, phone):
    r = req("GET", f"{BASE_NEW}/farmer_reward_service/v1/users/paymentAccounts/validate",
            params={"upiId": upi, "mobileNumber": phone})
    if r and r.status_code == 200:
        return r.json().get("data", {})
    return None

def link_upi(upi, phone):
    r = req("PUT", f"{BASE_NEW}/farmer_reward_service/v1/users/{state['registered_user_id']}/paymentAccounts",
            json={"mobileNumber": phone, "paymentMethod": "UPI", "paymentPlatform": "PHONEPE",
                  "upiId": upi, "userId": state["registered_user_id"]})
    return r is not None and r.status_code == 200

def claim_payout(reward_id, upi):
    r = req("POST", f"{BASE_NEW}/farmer_reward_service/v1/reward/payments/payout",
            json={"paymentMethod": "UPI", "registeredUserId": state["registered_user_id"],
                  "rewardEventId": reward_id, "upiId": upi})
    if r and r.status_code == 200:
        return r.json().get("data", {})
    return None

def payout_status(reward_id):
    r = req("POST", f"{BASE_NEW}/farmer_reward_service/v1/reward/payout/status",
            json={"registeredUserId": state["registered_user_id"], "rewardEventId": reward_id})
    if r and r.status_code == 200:
        return r.json().get("data", {})
    return None

def poll_until_done(reward_id, max_polls=40, interval=POLL_INTERVAL):
    print(title(f"\n⏳ Polling payout → {reward_id}"))
    last_status = None
    for i in range(1, max_polls + 1):
        d = payout_status(reward_id)
        if not d:
            time.sleep(interval)
            continue
        status = d.get("status", "?")
        msg = d.get("messageTitle", "")
        txt = d.get("rewardText", "")
        if status != last_status:
            print(ok(f"  [{i}/{max_polls}] {status} | {msg} | {txt}"))
            last_status = status
        else:
            print(info(f"  [{i}/{max_polls}] {status} ..."))

        if status in ("SUCCESS", "PAID", "COMPLETED", "CLAIM_IN_PROCESS", "PENDING", "IN_PROGRESS"):
            print(ok(f"\n🎉 Work Done! Status = {status}"))
            return True
        if status in ("FAILED", "REJECTED", "CANCELLED"):
            print(err(f"\n❌ FAILED: {msg}"))
            return False
        time.sleep(interval)
    print(warn("\n⚠️ Timeout"))
    return False

def ask_upi_when_needed():
    print(title("\n💳 Scratch card Mila! Ab UPI chahiye"))
    upi = input(info("🏦 UPI ID: ")).strip()
    if "@" not in upi:
        print(err("❌ Invalid UPI"))
        return None
    v = validate_upi(upi, state["phone"])
    if not v:
        print(err("❌ UPI validation failed"))
        return None
    print(ok(f"✅ {v.get('customerName')} | {v.get('status')}"))
    link_upi(upi, state["phone"])
    return upi

def process_reward(card, upi_holder):
    reward_id = card["rewardId"]
    print(title(f"\n🎯 {card.get('scratchCardTitle', '?')}"))
    print(debug(f"rewardId = {reward_id}"))

    if not card.get("scratchedDate"):
        print(info("→ Scratching..."))
        s = scratch_card(reward_id)
        if not s:
            print(err("❌ Scratch failed"))
            return False
        print(ok(f"🎁 {s.get('rewardText')} | {s.get('status')}"))
        card.update(s)

    if upi_holder.get("upi") is None:
        upi = ask_upi_when_needed()
        if not upi:
            return False
        upi_holder["upi"] = upi
    upi = upi_holder["upi"]

    status = card.get("status", "")
    if status == "UNCLAIMED":
        print(info("→ Claiming..."))
        c = claim_payout(reward_id, upi)
        if not c:
            print(err("❌ Claim failed"))
            return False
        print(ok(f"✅ Claim | {c.get('paymentStatus')}"))
        status = c.get("paymentStatus", "CLAIM_IN_PROCESS")

    if status in ("CLAIM_IN_PROCESS", "PENDING", "IN_PROGRESS", "SUCCESS", "PAID", "COMPLETED"):
        return poll_until_done(reward_id)
    return False

# ============================================================
# POLLING
# ============================================================
def polling_loop():
    print(title(f"\n🔄 Polling every {POLL_INTERVAL}s"))
    print(info("   Ctrl+C to stop\n"))
    cycle = 0
    paid = 0
    upi_holder = {"upi": None}

    while True:
        cycle += 1
        ts = datetime.now().strftime("%H:%M:%S")
        print(title(f"\n{'─'*60}"))
        print(title(f"🔄 Cycle #{cycle} | {ts} | PAID={paid}"))
        print(title(f"{'─'*60}"))

        if cycle % 5 == 0:
            if not validate_session():
                print(warn("⚠️ Session expired"))
                return

        cards = get_unclaimed()
        if not cards:
            bal = get_balance()
            print(warn(f"⚠️ No scratch card | Coins={bal}"))
            time.sleep(POLL_INTERVAL)
            continue

        print(ok(f"🎁 {len(cards)} scratch card(s) mila!"))
        for c in cards:
            try:
                if process_reward(c, upi_holder):
                    paid += 1
                time.sleep(2)
            except Exception as e:
                print(err(f"❌ {e}"))
        time.sleep(POLL_INTERVAL)

# ============================================================
# MAIN
# ============================================================
def main_menu():
    print(f"\n{C.MAGENTA}{C.BOLD}{'='*60}")
    print("   FarmRise v4.3 — Fixed Device + Full Live Debug")
    print(f"{'='*60}{C.RESET}")
    print(info(" 1 → New Account"))
    print(info(" 2 → Login Existing"))
    print(info(" 3 → Force fresh login"))
    print(info(" 0 → Exit\n"))
    return input(info("Choose [0-3]: ")).strip()

def flow_login_new():
    if not acquire_user(): return False
    phone = input(info("📱 Phone: ")).strip()
    if len(phone) != 10 or not phone.isdigit(): return False
    if not send_otp(phone): return False
    return get_otp_with_retry(phone)

def main():
    choice = main_menu()
    if choice == "0": return
    if choice == "1":
        if not flow_login_new(): return
    elif choice == "2":
        if not load_session() or not validate_session():
            print(warn("Session expired — new login"))
            if not flow_login_new(): return
    elif choice == "3":
        delete_session()
        if not flow_login_new(): return
    else: return

    print(title("\n=== Profile ==="))
    get_profile()
    print(ok(f"💰 Coins = {get_balance()}"))

    do_track_twice()

    print(title("\n=== Polling start ==="))
    try:
        polling_loop()
    except KeyboardInterrupt:
        print(f"\n{err('🛑 Stopped')}")
        save_session()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{err('🛑 Exit')}")
        save_session()
    except Exception as e:
        print(f"\n{err(f'💥 {e}')}")
