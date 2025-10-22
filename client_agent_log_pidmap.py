# client_agent_log_pidmap.py
# Log-only takip + PID -> process cmdline mapping
# Usage: python3 client_agent_log_pidmap.py
# Requires: requests

import re, subprocess, time, requests
from datetime import datetime

# ---------- AYARLAR ----------
webhook_url = "https://discord.com/api/webhooks/1416568811141988495/4-I2qf1l6ggkHcjg7xasLskM4-6CP-iuO3RJ9BWp0FBUn8EVWF9oKmhPxWaLJux45m1h"
interval = 10  # log kontrol periyodu (saniye)
keywords = ["bağlantı koptu", "connection lost", "disconnected", "respawn", "login-disconnected", "connectifdisconnected", "showrespawnmessagebox"]
reported_entries = set()
# --------------------------------

pid_regex = re.compile(r'\((\d+)\)')  # log satırındaki (PID)

def run(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=8)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def tail_log_and_find():
    out = run("logcat -d -v time | tail -n 1200")
    if not out:
        return []
    lines = out.splitlines()
    matches = []
    low = "\n".join(lines).lower()
    for kw in keywords:
        # find all occurrences of keyword lines
        idx = 0
        while True:
            idx = low.find(kw.lower(), idx)
            if idx == -1:
                break
            # get the whole line
            start = low.rfind("\n", 0, idx) + 1
            end = low.find("\n", idx)
            if end == -1: end = len(low)
            # original-case line from lines list (approx)
            # compute which line index in lines
            prefix = low[:start]
            line_no = prefix.count("\n")
            line = lines[line_no].strip()
            if line and line not in reported_entries:
                matches.append(line)
                reported_entries.add(line)
            idx = end
    return matches

def extract_pid(line):
    m = pid_regex.search(line)
    if m:
        return m.group(1)
    return None

def probe_process(pid):
    info = {"pid": pid, "cmdline": None, "cwd": None, "environ": None}
    # Try /proc/<pid>/cmdline
    cmd = f"cat /proc/{pid}/cmdline 2>/dev/null || true"
    out = run(cmd).strip()
    if out:
        # cmdline is null-separated; replace \x00 with spaces
        info["cmdline"] = out.replace("\x00", " ").strip()
    # Try ps to get args (some systems)
    if not info["cmdline"]:
        out2 = run(f"ps -p {pid} -o args= 2>/dev/null || true").strip()
        if out2:
            info["cmdline"] = out2
    # cwd (may give path with config or account)
    out3 = run(f"readlink -f /proc/{pid}/cwd 2>/dev/null || true").strip()
    if out3:
        info["cwd"] = out3
    # environ (may contain env vars with account names)
    out4 = run(f"tr '\\0' '\\n' < /proc/{pid}/environ 2>/dev/null || true").strip()
    if out4:
        info["environ"] = out4
    return info

def guess_account_from_info(info):
    # heuristics: search for typical patterns in cmdline/cwd/environ
    targets = []
    for k in ("cmdline", "cwd", "environ"):
        v = info.get(k)
        if not v:
            continue
        # common patterns: username, account, uid=, --user=, /data/data/.../files/<account>
        m = re.search(r'([A-Za-z0-9_.-]{3,40})', v)
        if m:
            targets.append((k, m.group(1)))
        # explicit patterns
        m2 = re.search(r'(--user=|user=|account=|acct=)([A-Za-z0-9_.-]+)', v, flags=re.I)
        if m2:
            return m2.group(2)
        m3 = re.search(r'/data/data/[^/]+/files/([^/\s]+)', v)
        if m3:
            return m3.group(1)
    # return best candidate or None
    if targets:
        # prefer cmdline candidates
        for k,c in targets:
            if k == "cmdline":
                return c
        return targets[0][1]
    return None

def post(webhook, content):
    try:
        requests.post(webhook, json={"content": content}, timeout=8)
    except Exception as e:
        print("Discord gönderilemedi:", e)

def build_message(line, pid, procinfo, account_guess):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"**UGTakip — Log Uyarısı** ({t})"]
    lines.append(f"> `{line}`")
    if pid:
        lines.append(f"- PID: {pid}")
    if account_guess:
        lines.append(f"- Tahmini hesap / client: **{account_guess}**")
    if procinfo.get("cmdline"):
        lines.append(f"- cmdline: `{procinfo['cmdline']}`")
    if procinfo.get("cwd"):
        lines.append(f"- cwd: `{procinfo['cwd']}`")
    return "\n".join(lines)

def main_loop():
    print("Log-only agent başlatılıyor... (PID mapping aktif)")
    while True:
        matches = tail_log_and_find()
        for line in matches:
            pid = extract_pid(line)
            procinfo = {"pid": pid}
            account = None
            if pid:
                procinfo = probe_process(pid)
                account = guess_account_from_info(procinfo)
            msg = build_message(line, pid, procinfo, account)
            post(webhook_url, msg)
            print("Gönderildi:", datetime.now().isoformat(), "pid:", pid, "acct:", account)
        time.sleep(interval)

if __name__ == "__main__":
    main_loop()
