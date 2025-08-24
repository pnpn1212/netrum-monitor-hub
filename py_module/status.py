#!/usr/bin/env python3
import subprocess
import html
from py_module.notification import send_all
from py_module.config import cfg

LOG_PLATFORM = "both"            

def run_status():
    try:
        cmd = "ps aux | grep 'netrum-lite-node' | grep -v grep | tail -n 1 || echo 'stopped'"
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True, 
            text=True
        )
       
        if result.stderr.strip():
            print(result.stderr.strip())

        output = result.stdout.strip()
        if not output:
            output = "stopped"

        msg_content = html.escape(output)
        msg = f"<b>📡  Node Status</b>\n<pre>{msg_content}</pre>"

        send_all(msg, cfg, platform=LOG_PLATFORM)

    except Exception as e:
        err_msg = f"<b>❌ Exception in Status</b>\n<pre>{html.escape(str(e))}</pre>"
        send_all(err_msg, cfg, platform=LOG_PLATFORM)
