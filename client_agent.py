# client_agent.py
# Termux üzerinde çalıştırılmak üzere hazırlanmıştır.
# Kullanım: python3 client_agent.py
# Gereksinimler: requests
# Termux'ta: pip install requests

import subprocess
import time
import requests
from datetime import datetime

# ---------- AYARLAR (burayı kendine göre değiştir) ----------
webhook_url = "https://discord.com/api/webhooks/1416568811141988495/4-I2qf1l6ggkHcjg7xasLskM4-6CP-iuO3RJ9BWp0FBUn8EVWF9oKmhPxWaLJux45m1h"  # kendi webhook
interval = 30  # saniye

# Oyun paketi isimleri ve insan okunur isimler
oyunlar = {
    "com.revenger.one": "Revenger 1",
    "com.revenger.two": "Revenger 2",
    "com.revenger.three": "Revenger 3",
}

# logcat'te aranacak anahtar kelimeler (küçük harfe çevirerek kontrol edilir)
keywords = ["bağlantı koptu", "connection lost", "disconnected", "respawn"]

# ----------------------------------------------------------------

# İç hafıza: daha önce bildirilen log satırları (duplicate engelleme)
reported_logs = set()

def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=8)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def check_pid(pkg):
    # pidof ile paket çalışıyorsa PID döner
    out = run_cmd(f"pidof {pkg}")
    return out.strip()

def check_activity_has_package(pkg):
    # dumpsys activity top -> en üst aktiviteyi getirip paketi içerip içermediğine bak
    out = run_cmd("dumpsys activity top")
    return pkg in out

def check_window_contains(pkg):
    # dumpsys window windows -> pencerelerde paket adı varsa
    out = run_cmd("dumpsys window windows")
    return pkg in out

def scan_logcat_for_keywords():
    # logcat'in son kısımlarını al, anahtar kelimelere bak
    # Not: logcat erişimi cihazda kısıtlı olabilir
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
            # alınacak satırı çıkaralım (en yakın newline'larla)
            # basit yaklaşım: ortaya çıkan konumdan sola/sağa bakarak satırı al
            start = lower.rfind("\n", 0, idx) + 1
            end = lower.find("\n", idx)
            if end == -1:
                end = len(lower)
            line = out[start:end].strip()
            # duplicate kontrolü
            if line and line not in reported_logs:
                reported_logs.add(line)
                found.append(line)
            idx = end
    return found

def post_to_discord(content):
    try:
        data = {"content": content}
        requests.post(webhook_url, json=data, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)

def format_status(status_map, logs):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"**UGTakip — Oyun Durum Raporu** ({now})"]
    for pkg, info in status_map.items():
        lines.append(f"- **{info['name']}**: {info['state']} {info.get('extra','')}")
    if logs:
        lines.append("\n**Yeni Log Uyarıları:**")
        for l in logs:
            # kısalt (çok uzunsa)
            txt = l if len(l) < 800 else l[:800] + "…"
            lines.append(f"> {txt}")
    return "\n".join(lines)

def main_loop():
    while True:
        status = {}
        for pkg, pretty in oyunlar.items():
            pid = check_pid(pkg)
            active_by_pid = bool(pid)
            active_by_activity = check_activity_has_package(pkg)
            active_by_window = check_window_contains(pkg)
            # karar: eğer herhangi biri true ise "açık" kabul et
            açık = active_by_pid or active_by_activity or active_by_window
            extra = []
            if active_by_pid:
                extra.append(f"PID={pid}")
            if active_by_activity:
                extra.append("Aktivite açık")
            if active_by_window:
                extra.append("Pencere var")
            status[pkg] = {
                "name": pretty,
                "state": "Çalışıyor ✅" if açık else "Kapalı ❌",
                "extra": "(" + ", ".join(extra) + ")" if extra else ""
            }

        # logcat taraması
        new_logs = scan_logcat_for_keywords()

        # Eğer herhangi bir oyun kapalıysa veya yeni log varsa bildirim at (koşulu özelleştirebilirsin)
        should_notify = any(s["state"].startswith("Kapalı") for s in status.values()) or bool(new_logs)

        if should_notify:
            msg = format_status(status, new_logs)
            post_to_discord(msg)
            print("Gönderildi:", datetime.now().isoformat())

        # konsola kısa çıktı (debug)
        for s in status.values():
            print(f"{s['name']}: {s['state']} {s['extra']}")
        if new_logs:
            print("Yeni loglar:", len(new_logs))

        time.sleep(interval)

if __name__ == "__main__":
    print("UGTakip agent başlatılıyor...")
    main_loop()
