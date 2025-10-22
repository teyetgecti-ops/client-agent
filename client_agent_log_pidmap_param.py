#!/data/data/com.termux/files/usr/bin/python3
import subprocess
import time
import requests
import argparse

# ---------- ARGÜMANLAR ----------
parser = argparse.ArgumentParser(description="UGTakip UIAutomator Agent")
parser.add_argument("--ugname", required=True, help="UG cihaz adı (örn. UG1)")
parser.add_argument("--webhook", required=True, help="Discord webhook URL")
parser.add_argument("--interval", type=int, default=30, help="Log kontrol intervali (saniye)")
args = parser.parse_args()

ug_name = args.ugname
webhook_url = args.webhook
interval = args.interval

# ---------- ANAHTAR KELİMELER ----------
keywords = ["disconnected", "respawn"]
reported_lines = set()  # Aynı log tekrar göndermesin

# ---------- YARDIMCI FONKSİYONLAR ----------
def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=8)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def scan_logcat_for_keywords():
    out = run_cmd("logcat -d -v time | tail -n 800")
    found_keywords = []
    if not out:
        return found_keywords

    lower = out.lower()
    for kw in keywords:
        idx = 0
        while True:
            idx = lower.find(kw, idx)
            if idx == -1:
                break
            start = lower.rfind("\n", 0, idx) + 1
            end = lower.find("\n", idx)
            if end == -1:
                end = len(lower)
            line = out[start:end].strip()
            # Sadece keyword gönder
            if line and line not in reported_lines:
                reported_lines.add(line)
                found_keywords.append(kw.capitalize())  # Disconnected / Respawn
            idx = end
    return found_keywords

def post_to_discord(message):
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)

# ---------- ANA DÖNGÜ ----------
print(f"UGTakip agent başlatılıyor... UG: {ug_name}")
while True:
    new_keywords = scan_logcat_for_keywords()
    for kw in new_keywords:
        msg = f"{ug_name}: {kw}"
        post_to_discord(msg)
        print(msg)
    time.sleep(interval)
