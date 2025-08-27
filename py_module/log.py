#!/usr/bin/env python3
import subprocess
import html
from py_module.notification import send_all
from py_module.config import cfg
from py_module.language import translations, get_lang

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

        lang = get_lang()
        t_dict = translations.get(lang, translations["en"])

        all_output = result.stdout
        if result.stderr.strip():
            all_output += "\n" + result.stderr

        lines = [html.escape(line) for line in all_output.splitlines() if line.strip()]

        lines = lines[-BUFFER_LINES:]

        msg_content = "\n".join(lines)

        if msg_content:
            msg = f"<b>📜 {t_dict['logs_logs']}</b>\n<pre>{msg_content}</pre>"
            send_all(msg, cfg, platform=LOG_PLATFORM)
        else:
            msg = f"<b>📜 {t_dict['logs_logs']}</b>\n<pre>⚠️ {t_dict['no_logs']}</pre>"
            send_all(msg, cfg, platform=LOG_PLATFORM)

    except Exception as e:
        err_msg = f"<b>❌ {t_dict['logs_exception']}</b>\n<pre>{html.escape(str(e))}</pre>"
        send_all(err_msg, cfg, platform=LOG_PLATFORM)






