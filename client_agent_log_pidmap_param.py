#!/data/data/com.termux/files/usr/bin/python3
import subprocess
import time
import requests
import argparse

# ---------- ARGÜMANLAR ----------
parser = argparse.ArgumentParser(description="UGTakip UIAutomator Agent")
parser.add_argument("--ugname", required=True, help="UG cihaz adı (örn. UG1)")
parser.add_argument("--webhook", required=True, help="Discord webhook URL")
parser.add_argument("--interval", type=int, default=30, help="Log kontrol aralığı (saniye)")
args = parser.parse_args()

ug_name = args.ugname
webhook_url = args.webhook
interval = args.interval

# ---------- ANAHTAR KELİMELER ----------
keywords = ["disconnected", "respawn"]
reported = set()

# ---------- KOMUT YARDIMCISI ----------
def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=8)
        return out.decode(errors="ignore")
    except Exception:
        return ""

# ---------- LOG TARAMA ----------
def scan_logs():
    out = run_cmd("logcat -d -v time | tail -n 500")
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
            line = out[lower.rfind('\n', 0, idx)+1: lower.find('\n', idx)].strip()
            if line and line not in reported:
                reported.add(line)
                found.append(kw.capitalize())
            idx += 1
    return list(set(found))

# ---------- DİSCORD GÖNDERİCİ ----------
def send_to_discord(msg):
    try:
        requests.post(webhook_url, json={"content": msg}, timeout=10)
    except:
        pass

# ---------- ANA DÖNGÜ ----------
print(f"UGTakip başlatıldı ✅  |  Cihaz: {ug_name}")
while True:
    logs = scan_logs()
    if logs:
        msg = f"{ug_name}: {', '.join(logs)}"
        send_to_discord(msg)
        print(msg)
    time.sleep(interval)
