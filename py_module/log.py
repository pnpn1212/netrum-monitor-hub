#!/usr/bin/env python3
import subprocess
import html
from py_module.notification import send_all
from py_module.config import cfg

CONTAINER_NAME = "netrum_monitor"
BUFFER_LINES = 10 
LOG_PLATFORM = "both"

def run_logs():
    try:
        result = subprocess.run(
            ["docker", "logs", f"--tail={BUFFER_LINES}", CONTAINER_NAME],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.stderr.strip():
            print(result.stderr.strip())

        lines = [html.escape(line) for line in result.stdout.splitlines() if line.strip()]

        if lines:
            msg_content = "\n".join(lines)
            msg = f"<b>📜 Logs</b>\n<pre>{msg_content}</pre>"
            send_all(msg, cfg, platform=LOG_PLATFORM)
        else:
            send_all("<b>📜 Logs</b>\n<pre>⚠️ No logs found</pre>", cfg, platform=LOG_PLATFORM)

    except Exception as e:
        err_msg = f"<b>❌ Exception in Logs</b>\n<pre>{html.escape(str(e))}</pre>"
        send_all(err_msg, cfg, platform=LOG_PLATFORM)
