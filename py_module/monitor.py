#!/usr/bin/env python3
import subprocess
import time
import re
import logging
from datetime import datetime
from py_module.config import LIVE_LOG_JS, NETRUM_NODE_DIR, cfg, DAILY_STATS, tz
from py_module.notification import send_all
from py_module.utils import countdown, get_timeout_from_file
from py_module.parse_log import parse_log_line

def monitor_log():
    retry_count = 0

    while True:
        logging.warning(f'Retry #{retry_count} - Starting netrum-mining-log...')
        proc = subprocess.Popen(
            ['node', str(LIVE_LOG_JS)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=NETRUM_NODE_DIR
        )
        start_time = time.time()
        mined_found = False

        for raw_line in iter(proc.stdout.readline, b''):
            line = raw_line.decode(errors='ignore').strip()
            if not line:
                continue

            idx = line.find("⏱️")
            if idx != -1:
                line = line[idx:]

            if 'Error fetching status' in line:
                proc.kill()
                break

            if 'Mined:' in line:
                mined_found = True
                print(line, flush=True)

                parsed = parse_log_line(line)
                try:
                    mined_val = float(parsed.get("mined", 0.0))
                except:
                    mined_val = 0.0
                DAILY_STATS['mined'] = mined_val

                msg = (
                    "<b>📊 Mining Update</b>\n"
                    "<pre>"
                    f"⏰ Remain: {parsed['time']}\n"
                    f"🏁 Load:   {parsed['progress']}\n"
                    f"💎 Mined:  {mined_val}\n"
                    f"⏩ Speed:  {parsed['speed']}\n"
                    f"🌐 Status: {parsed['status']}\n"
                    "</pre>"
                )
                send_all(msg, cfg, platform='both')

                proc.kill()
                break

            if time.time() - start_time > get_timeout_from_file() * 60:
                proc.kill()
                break

        if mined_found:
            retry_count = 0
            countdown()
            continue
        else:
            retry_count += 1
            now = datetime.now(tz).strftime("%H:%M:%S - %d/%m/%Y")
            print(f"[{now}] 🕒 Wait 00:30 try again netrum-mining-log...", flush=True)
            time.sleep(30)
