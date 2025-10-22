# client_agent_log_pidmap_sade.py
# Termux üzerinde çalışacak şekilde hazırlandı
# Amaç: sadece belirlenen log kelimelerini gördüğünde UG adına bildirim göndermek
# Birden fazla log kelimesi olsa bile tek satır halinde Discord'a yolluyor

import subprocess
import time
import requests
import os

# ---------- AYARLAR ----------
webhook_url = "https://discord.com/api/webhooks/1416568811141988495/4-I2qf1l6ggkHcjg7xasLskM4-6CP-iuO3RJ9BWp0FBUn8EVWF9oKmhPxWaLJux45m1h"
interval = 30  # saniye

# Loglarda aranacak kelimeler (küçük harfe çevirip kontrol edilecek)
keywords = ["disconnected", "respawn"]

# UG cihaz adı (başlatırken environment variable ile verilecek)
ug_name = os.getenv("UG_NAME", "Bilinmeyen UG")

# Daha önce bildirilen logları tekrar göndermemek için
reported_logs = set()

# ---------- FONKSİYONLAR ----------

def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=8)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def scan_logcat_for_keywords():
    out = run_cmd("logcat -d -v time | tail -n 800")
    found = set()
    if not out:
        return found
    lower = out.lower()
    for kw in keywords:
        if kw in lower and kw not in reported_logs:
            reported_logs.add(kw)
            found.add(kw.capitalize())  # "Disconnected" veya "Respawn"
    return found

def post_to_discord(events):
    if not events:
        return
    msg = f"{ug_name}: " + ", ".join(events)
    try:
        requests.post(webhook_url, json={"content": msg}, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)

# ---------- ANA DÖNGÜ ----------

def main_loop():
    while True:
        events = scan_logcat_for_keywords()
        if events:
            post_to_discord(events)
            print(f"Gönderildi: {ug_name} -> {', '.join(events)}")
        time.sleep(interval)

if __name__ == "__main__":
    print(f"UGTakip agent başlatılıyor: {ug_name}")
    main_loop()
