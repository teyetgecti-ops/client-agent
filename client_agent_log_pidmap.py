# UGTakip_UIA_param.py
import argparse
import time
import requests
from datetime import datetime

# ---------- AYARLAR ----------
parser = argparse.ArgumentParser()
parser.add_argument("--ugname", required=True, help="UG cihaz adı")
parser.add_argument("--webhook", required=True, help="Discord webhook URL")
parser.add_argument("--interval", type=int, default=30, help="Kontrol aralığı saniye")
args = parser.parse_args()

ug_name = args.ugname
webhook_url = args.webhook
interval = args.interval

# Loglarda bakılacak anahtar kelimeler
keywords = ["disconnected", "respawn"]
reported_logs = set()

def scan_logcat_for_keywords():
    import subprocess
    out = subprocess.getoutput("logcat -d -v time | tail -n 800")
    found = []
    if not out:
        return found
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
            if line and line not in reported_logs:
                reported_logs.add(line)
                found.append(line)
            idx = end
    return found

def post_to_discord(content):
    try:
        requests.post(webhook_url, json={"content": content}, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)

def main_loop():
    while True:
        new_logs = scan_logcat_for_keywords()
        if new_logs:
            # Her log için UG adı ekle
            msg = "\n".join([f"{ug_name}: {l}" for l in new_logs])
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_msg = f"UGTakip — Log Uyarısı ({now})\n{msg}"
            post_to_discord(full_msg)
            print(full_msg)
        time.sleep(interval)

if __name__ == "__main__":
    print(f"UGTakip agent başlatıldı: {ug_name}")
    main_loop()
