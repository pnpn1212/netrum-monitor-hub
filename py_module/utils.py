#!/usr/bin/env python3
import os
import time
from datetime import datetime
from py_module.config import tz, cfg

NETRUM_FILE = ".netrum"
DEFAULT_TIMEOUT = 5

def get_timeout_from_file():
    timeout = DEFAULT_TIMEOUT
    lines = []

    if os.path.exists(NETRUM_FILE):
        with open(NETRUM_FILE) as f:
            lines = [line.rstrip() for line in f]
            for line in lines:
                if line.startswith("TIMEOUT_MIN="):
                    try:
                        timeout = int(line.strip().split("=")[1])
                    except ValueError:
                        timeout = DEFAULT_TIMEOUT
                    break

    if not any(line.startswith("TIMEOUT_MIN=") for line in lines):
        lines.append(f"TIMEOUT_MIN={DEFAULT_TIMEOUT}")
        with open(NETRUM_FILE, "w") as f:
            for line in lines:
                f.write(f"{line}\n")
        cfg['TIMEOUT_MIN'] = str(DEFAULT_TIMEOUT)

    return timeout

def set_timeout(minutes: int):
    minutes = max(5, min(1440, minutes))
    lines = []
    if os.path.exists(NETRUM_FILE):
        with open(NETRUM_FILE) as f:
            lines = [line.rstrip() for line in f if not line.startswith("TIMEOUT_MIN=")]
    lines.append(f"TIMEOUT_MIN={minutes}")
    with open(NETRUM_FILE, "w") as f:
        for line in lines:
            f.write(f"{line}\n") 
    cfg['TIMEOUT_MIN'] = str(minutes)
    return minutes

def get_timeout_min():
    try:
        return int(cfg.get('TIMEOUT_MIN', get_timeout_from_file()))
    except ValueError:
        return get_timeout_from_file()

def countdown(elapsed=0):
    while True:
        timeout = get_timeout_min() * 60  # lấy mới mỗi vòng
        if elapsed >= timeout:
            break

        now_str = datetime.now(tz).strftime("%H:%M:%S - %d/%m/%Y")
        remain = timeout - elapsed
        hh = remain // 3600
        mm = (remain % 3600) // 60
        ss = remain % 60
        hms = f"{hh:02}:{mm:02}:{ss:02}"
        print(f"[{now_str}] 🕒 Wait time_out {hms} run netrum-mining-log...", flush=True)
        time.sleep(1)
        elapsed += 1
