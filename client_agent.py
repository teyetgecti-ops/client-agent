# client_agent_monitor.py
# Termux üzerinde çalıştırılmak üzere güncellendi
# Gereksinimler: requests, uiautomator erişimi tercih edilir

import subprocess
import time
import requests
from datetime import datetime

# ---------- AYARLAR ----------
webhook_url = "https://discord.com/api/webhooks/1416568811141988495/4-I2qf1l6ggkHcjg7xasLskM4-6CP-iuO3RJ9BWp0FBUn8EVWF9oKmhPxWaLJux45m1h"
interval = 30  # saniye

# Oyun paketleri ve isimleri
oyunlar = {
    "com.revengeronlineworle": "Revenger 1",
    "com.revengeronlineworlf": "Revenger 2",
    "com.revengeronlineworlg": "Revenger 3",  # eğer varsa
}


# Loglarda veya UI metinlerinde aranacak anahtar kelimeler
keywords = ["bağlantı koptu", "connection lost", "disconnected", "respawn"]

# Daha önce bildirilen loglar
reported_logs = set()

# ---------- FONKSİYONLAR ----------

def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=10)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def check_pid(pkg):
    out = run_cmd(f"pidof {pkg}")
    return out.strip()

def check_ui_for_keywords():
    """uiautomator dump ile ekran metinlerini al ve keywords kontrol et"""
    run_cmd("uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1")
    content = run_cmd("cat /sdcard/window_dump.xml 2>/dev/null")
    found = []
    if not content:
        return found
    lower = content.lower()
    for kw in keywords:
        if kw.lower() in lower:
            found.append(kw)
    return found

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

def format_status(status_map, logs, ui_alerts):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"**UGTakip — Oyun Durum Raporu** ({now})"]
    for pkg, info in status_map.items():
        lines.append(f"- **{info['name']}**: {info['state']} {info.get('extra','')}")
    if ui_alerts:
        lines.append("\n**UI Uyarıları:** " + ", ".join(ui_alerts))
    if logs:
        lines.append("\n**Yeni Log Uyarıları:**")
        for l in logs:
            txt = l if len(l) < 800 else l[:800] + "…"
            lines.append(f"> {txt}")
    return "\n".join(lines)

# ---------- ANA DÖNGÜ ----------

def main_loop():
    while True:
        status = {}
        for pkg, pretty in oyunlar.items():
            pid = check_pid(pkg)
            aktif = bool(pid)
            status[pkg] = {
                "name": pretty,
                "state": "Çalışıyor ✅" if aktif else "Kapalı ❌",
                "extra": f"(PID={pid})" if aktif else ""
            }

        # UI kontrolü
        ui_alerts = check_ui_for_keywords()

        # Log kontrolü
        new_logs = scan_logcat_for_keywords()

        # Eğer herhangi oyun kapalıysa veya yeni log/UI varsa gönder
        should_notify = any(s["state"].startswith("Kapalı") for s in status.values()) or bool(new_logs) or bool(ui_alerts)
        if should_notify:
            msg = format_status(status, new_logs, ui_alerts)
            post_to_discord(msg)
            print("Gönderildi:", datetime.now().isoformat())

        # Konsol debug
        for s in status.values():
            print(f"{s['name']}: {s['state']} {s['extra']}")
        if new_logs:
            print("Yeni loglar:", len(new_logs))
        if ui_alerts:
            print("UI uyarıları:", ui_alerts)

        time.sleep(interval)

if __name__ == "__main__":
    print("UGTakip agent başlatılıyor...")
    main_loop()
