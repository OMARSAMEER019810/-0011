#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_faucet_ready.py – نسخة معدّلة لتعمل على Render.com كـ Background Worker
"""

import re
import sys
import time
import requests
from bs4 import BeautifulSoup

# ——— إعدادات المستخدم ———
COOKIES = {
    "login": "1",
    "user":  "519403573317"
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/124.0.0.0 Safari/537.36"
)
BASE_URL           = "https://faucetearner.org"
FIXED_WAIT_SECONDS = 60  # دقيقة كاملة بين المحاولات

# ——— إعدادات البوت تيليجرام ———
TELEGRAM_TOKEN = "7331724197:AAE_UyDwN71iSq4As4cgnD9MRkzaISd3YsQ"
CHAT_ID = "6743860455"

# ——— إرسال رسالة للبوت ———
def send_telegram_message(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        if not response.ok:
            print(f"⚠️ فشل إرسال الرسالة للبوت: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ فشل إرسال الرسالة للبوت: {e}")

# ——— وظائف مساعدة ———
def start_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Referer": f"{BASE_URL}/faucet.php"
    })
    for k, v in COOKIES.items():
        s.cookies.set(k, v)
    return s

amount_rx = re.compile(r"([\d.]+)\s*XRP", re.I)

def extract_amount(text):
    m = amount_rx.search(text)
    return float(m.group(1)) if m else None

def fetch_balance(sess):
    try:
        pg = sess.get(f"{BASE_URL}/dashboard.php", timeout=10)
    except requests.RequestException:
        return None
    soup = BeautifulSoup(pg.text, "html.parser")
    bal_tag = soup.find(text=amount_rx)
    return extract_amount(bal_tag) if bal_tag else None

def claim_once(sess):
    try:
        resp = sess.post(f"{BASE_URL}/api.php?act=faucet", timeout=10)
    except requests.RequestException as err:
        print(f"\n⚠️  فشل طلب المطالبة: {err}")
        return None, None

    earned = extract_amount(resp.text)
    balance = fetch_balance(sess)
    return earned, balance

def countdown(seconds):
    print(f"⌛ الانتظار {seconds} ثانية ...")
    time.sleep(seconds)

def main():
    print("🪙 بدأ برنامج المطالبة التلقائية – Ctrl+C للإيقاف\n")
    session = start_session()
    total_session = 0.0

    while True:
        try:
            earned, balance = claim_once(session)

            if earned is not None:
                total_session += earned
                msg = f"✅ ربحت {earned:.6f} XRP | الرصيد الآن ≈ {balance or '؟'} XRP | مجموع الجلسة = {total_session:.6f} XRP"
                print(msg)
                send_telegram_message(msg)
            else:
                fail_msg = "❌ لم تنجح المطالبة هذه المرّة"
                print(fail_msg)
                send_telegram_message(fail_msg)

            countdown(FIXED_WAIT_SECONDS)
        except Exception as e:
            print(f"⚠️ حصل خطأ غير متوقع: {e}")
            countdown(FIXED_WAIT_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البرنامج يدويًا")
        sys.exit(0)
