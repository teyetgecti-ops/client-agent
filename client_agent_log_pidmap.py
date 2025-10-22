import subprocess
import time
import requests

# UG cihaz adı ve Discord webhook parametreleri
UG_NAME = "UG1"  # Başlatırken --ugname ile değiştirebilirsin
WEBHOOK = "https://discord.com/api/webhooks/1416568811141988495/4-I2qf1l6ggkHcjg7xasLskM4-6CP-iuO3RJ9BWp0FBUn8EVWF9oKmhPxWaLJux45m1h"

# Bildirilecek log keywordleri
KEYWORDS = ["disconnected", "respawn"]

# Daha önce gönderilen logları takip etmek için set
reported_logs = set()

# Oyunun açılışındaki spam logları görmezden gelmek için süre (saniye)
STARTUP_IGNORE_SECONDS = 15
startup_time = time.time()

def run_cmd(cmd):
    """Shell komutunu çalıştırır ve çıktısını döner"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def scan_logcat_for_keywords():
    """Logcat'i tarar, keyword bulunan yeni logları döner"""
    out = run_cmd("logcat -d -v time | tail -n 800")
    found = []
    lower = out.lower()
    for kw in KEYWORDS:
        idx = 0
        while True:
            idx = lower.find(kw, idx)
            if idx == -1:
                break
            start = lower.rfind("\n", 0, idx) + 1
            end = lower.find("\n", idx)
            if end == -1: end = len(lower)
            line = out[start:end].strip()
            if line and line not in reported_logs:
                reported_logs.add(line)
                found.append(kw)  # Sadece keyword'u ekle
            idx = end
    return found

def post_to_discord(message):
    """Discord webhook ile mesaj gönderir"""
    requests.post(WEBHOOK, json={"content": message})

def main_loop():
    while True:
        # Açılış log spamını ignore et
        if time.time() - startup_time < STARTUP_IGNORE_SECONDS:
            time.sleep(1)
            continue

        new_logs = scan_logcat_for_keywords()
        if new_logs:
            for kw in new_logs:
                post_to_discord(f"{UG_NAME}: {kw.capitalize()}")

        time.sleep(30)  # Interval (başlatırken değiştirilebilir)

if __name__ == "__main__":
    print(f"{UG_NAME} UGTakip agent started...")
    main_loop()
