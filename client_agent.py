#!/data/data/com.termux/files/usr/bin/env python3
import time, subprocess, requests, uuid, os
from datetime import datetime

SERVER = "https://your-server.example.com/report"
INTERVAL = 30
WATCH_PACKAGES = ["com.example.client1","com.example.client2","com.another.client"]
ID_FILE = "/data/data/com.termux/files/home/.agent_device_id"

def get_device_id():
    if os.path.exists(ID_FILE):
        return open(ID_FILE).read().strip()
    else:
        did = str(uuid.uuid4())
        with open(ID_FILE,"w") as f:
            f.write(did)
        return did

def detect_running(pkg_list):
    running = []
    for pkg in pkg_list:
        out = subprocess.getoutput(f"pidof {pkg}")
        if out.strip():
            running.append(pkg)
    return running

def post_report(device_id, running):
    payload = {"device_id": device_id,"timestamp":datetime.utcnow().isoformat()+"Z","running":running}
    try:
        requests.post(SERVER,json=payload,timeout=5)
    except:
        pass

device_id = get_device_id()
while True:
    running = detect_running(WATCH_PACKAGES)
    post_report(device_id,running)
    print(datetime.now(), running)
    time.sleep(INTERVAL)
