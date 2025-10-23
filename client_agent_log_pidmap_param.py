#!/data/data/com.termux/files/usr/bin/python3
import subprocess
import time
import requests
import argparse
import os

# ---------- ARGÜMANLAR ----------
parser = argparse.ArgumentParser(description="UGTakip UIAutomator Agent")
parser.add_argument("--ugname", required=True, help="UG cihaz adı (örn. UG1)")
parser.add_argument("--interval", type=int, default=30, help="Log kontrol intervali (saniye)")
args = parser.parse_args()

ug_name = args.ugname
interval = args.interval

# ---------- SABİT WEBHOOK ----------
webhook_url = "https://discord.com/api/webhooks/1430676212489130216/lhHkzELmG00B8EcRJS8o7tPFLuNZ8Q0dHQygjCJ0xn8mzeIZtXCbG2EDQJD6FcorSBlN"

# ---------- ANAHTAR KELİMELER ----------
keywords = ["disconnected", "respawn"]
reported_logs = set()

# ---------- GÜNCELLEME ----------
GITHUB_URL = "https://raw.githubusercontent.com/teyetgecti-ops/client-agent/main/client_agent_log_pidmap_param.py"

def update_script():
    try:
        # GitHub'daki son sürümü indir
        tmp_file = "/data/data/com.termux/files/home/tmp_client_agent.py"
        subprocess.run(f"curl -L -o {tmp_file} {GITHUB_URL}", shell=True, check=True)
        # Mevcut script ile karşılaştır
        with open(tmp_file, "r") as f1, open(__file__, "r") as f2:
            if f1.read() != f2.read():
                os.replace(tmp_file, __file__)
                print("Script güncellendi, yeniden başlatılıyor...")
                os.execv(__file__, ["python3"] + os.sys.argv)
    except Exception as e:
        print("Otomatik güncelleme başarısız:", e)

# ---------- YARDIMCI FONKSİYONLAR ----------
def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def scan_logcat_for_keywords():
    out = run_cmd("logcat -d -v time | tail -n 200")  # daha az satır
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

def post_to_discord(message):
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)

# ---------- ANA DÖNGÜ ----------
print(f"UGTakip agent başlatılıyor... UG: {ug_name}")
loop_counter = 0
while True:
    loop_counter += 1
    # Otomatik güncelleme her 100 döngüde kontrol edilecek
    if loop_counter % 100 == 0:
        update_script()

    new_logs = scan_logcat_for_keywords()
    if new_logs:
        for l in new_logs:
            kw_found = [kw.capitalize() for kw in keywords if kw in l.lower()]
            if kw_found:
                msg = f"{ug_name}: {', '.join(kw_found)}"
                post_to_discord(msg)
                print(msg)
    time.sleep(interval)
