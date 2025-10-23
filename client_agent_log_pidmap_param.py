#!/data/data/com.termux/files/usr/bin/python3
import subprocess
import time
import requests
import argparse

# ---------- ARGÜMANLAR ----------
parser = argparse.ArgumentParser(description="UGTakip UIAutomator Agent")
parser.add_argument("--ugname", required=True, help="UG cihaz adı (örn. UG1)")
parser.add_argument("--interval", type=int, default=30, help="Log kontrol aralığı (saniye)")
args = parser.parse_args()

ug_name = args.ugname
interval = args.interval

# ---------- SABİT WEBHOOK ----------
webhook_url = "https://discord.com/api/webhooks/1430676212489130216/lhHkzELmG00B8EcRJS8o7tPFLuNZ8Q0dHQygjCJ0xn8mzeIZtXCbG2EDQJD6FcorSBlN"

# ---------- ANAHTAR KELİMELER ----------
keywords = ["disconnected", "respawn"]
ignore_phrases = ["fake disconnected", "simulated disconnect", "mock disconnect"]
reported_logs = set()

# ---------- YARDIMCI FONKSİYONLAR ----------
def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=8)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def scan_logcat_for_keywords():
    out = run_cmd("logcat -d -v time | tail -n 800")
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

            if any(phrase in line.lower() for phrase in ignore_phrases):
                idx = end
                continue

            if line and line not in reported_logs:
                reported_logs.add(line)
                found.append(line)
            idx = end
    return found

def post_to_discord(message):
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print("⚠️ Discord gönderilemedi:", e)

def clear_logcat():
    try:
        subprocess.run("logcat -c", shell=True, stderr=subprocess.DEVNULL)
    except Exception:
        pass

# ---------- ANA DÖNGÜ ----------
print(f"🚀 UGTakip agent başlatıldı! UG: {ug_name}")
start_time = time.time()

while True:
    new_logs = scan_logcat_for_keywords()

    if new_logs:
        hours_active = (time.time() - start_time) / 3600
        for l in new_logs:
            kw_found = [kw.capitalize() for kw in keywords if kw in l.lower()]
            if kw_found:
                msg = f"{ug_name}: {', '.join(kw_found)} — {hours_active:.1f} saattir sorunsuz çalıştı ✅"
                post_to_discord(msg)
                print(f"[!] 🔴 {msg}")

    clear_logcat()
    time.sleep(interval)
