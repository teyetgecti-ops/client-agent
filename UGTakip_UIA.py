import uiautomator2 as u2
import subprocess
import time
import requests
from datetime import datetime

# ---------- AYARLAR ----------
webhook_url = "https://discord.com/api/webhooks/1416568811141988495/4-I2qf1l6ggkHcjg7xasLskM4-6CP-iuO3RJ9BWp0FBUn8EVWF9oKmhPxWaLJux45m1h"
interval = 30  # saniye

oyunlar = {
    "com.revengeronlineworle": "Revenger 1",
    "com.revengeronlineworlf": "Revenger 2",
    "com.revengeronlineworlg": "Revenger 3",
}

keywords = [
    "bağlantı koptu",
    "connection lost",
    "disconnected",
    "respawn",
    "Login-Disconnected",
    "ConnectIfDisconnected",
    "ShowRespawnMessageBox"
]

reported_logs = set()

# ---------- FONKSİYONLAR ----------
def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=10)
        return out.decode(errors="ignore")
    except:
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
            idx = lower.find(kw.lower(), idx)
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

def format_status(status_map, logs):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"**UGTakip — Oyun Durum Raporu** ({now})"]
    for name, info in status_map.items():
        lines.append(f"- **{name}**: {info}")
    if logs:
        lines.append("\n**Yeni Log Uyarıları:**")
        for l in logs:
            txt = l if len(l) < 800 else l[:800] + "…"
            lines.append(f"> {txt}")
    return "\n".join(lines)

# ---------- ANA DÖNGÜ ----------
def main_loop():
    d = u2.connect()  # Termux cihaz ile bağlan
    while True:
        status = {}
        new_logs = scan_logcat_for_keywords()

        for pkg, name in oyunlar.items():
            try:
                info = d.app_info(pkg)
                aktif = True
            except:
                aktif = False

            if aktif:
                state = "Çalışıyor ✅"
            else:
                if any(kw.lower() in l.lower() for l in new_logs for kw in keywords):
                    state = "Kapalı ❌ ⚠️ Bağlantı uyarısı"
                else:
                    state = "Kapalı ❌"

            status[name] = state

        # Discord gönderimi
        should_notify = any("Kapalı" in s or "⚠️" in s for s in status.values())
        if should_notify:
            msg = format_status(status, new_logs)
            post_to_discord(msg)
            print("Gönderildi:", datetime.now().isoformat())

        # Konsol debug
        for name, s in status.items():
            print(f"{name}: {s}")
        if new_logs:
            print("Yeni loglar:", len(new_logs))

        time.sleep(interval)

if __name__ == "__main__":
    print("UGTakip UIAutomator agent başlatılıyor...")
    main_loop()
