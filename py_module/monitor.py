#!/usr/bin/env python3
import subprocess
import time
import re
import logging
from datetime import datetime
from py_module.language import translations, get_lang
from wcwidth import wcswidth
from py_module.config import LIVE_LOG_JS, NETRUM_NODE_DIR, cfg, DAILY_STATS, tz
from py_module.notification import send_all
from py_module.utils import countdown, get_timeout_from_file
from py_module.parse_log import parse_log_line

def monitor_log():
    retry_count = 0

    while True:
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

                lang = get_lang() 
                t_dict = translations.get(lang, translations["en"])

                labels = [
                    t_dict['remain'],
                    t_dict['load'],
                    t_dict['mined'],
                    t_dict['speed'],
                    t_dict['tasks'],
                    t_dict['status_monitor']
                ]

                max_label_len = max(wcswidth(label) for label in labels)

                msg = (
                    f"<b>📊 {t_dict['mining_update']}</b>\n"
                    "<pre>"
                    f"⏰ {t_dict['remain']:<{max_label_len}} | {parsed['time']}\n"
                    f"🏁 {t_dict['load']:<{max_label_len}} | {parsed['progress']}\n"
                    f"💎 {t_dict['mined']:<{max_label_len}} | {mined_val}\n"
                    f"⏩ {t_dict['speed']:<{max_label_len}} | {parsed['speed']}\n"
                    f"📦 {t_dict['tasks']:<{max_label_len}} | {parsed['tasks']}\n"
                    f"🌐 {t_dict['status_monitor']:<{max_label_len}} | {parsed['status']}\n"
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
        else:
            retry_count += 1
            now = datetime.now(tz).strftime("%H:%M:%S - %d/%m/%Y")
            logging.warning(f"[{now}] 🔁 Retry #{retry_count} in 00:30 → netrum-mining-log")
            time.sleep(30)
