#!/usr/bin/env python3
import subprocess, json, requests

def send_telegram(text, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    try:
        subprocess.run(['curl','-s','-X','POST',url,'-H','Content-Type: application/json','-d',json.dumps(payload)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f'Telegram send failed: {e}')

def send_discord(message, webhook):
    if not webhook: return
    try:
        payload = {"content": message.replace("<b>", "**").replace("</b>", "**")
                                     .replace("<pre>", "```").replace("</pre>", "```")}
        requests.post(webhook, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Error Send Discord: {e}")

def send_all(message, cfg, platform='both'):
    if platform in ('both','telegram'):
        send_telegram(message, cfg['TELEGRAM_BOT_TOKEN'], cfg['TELEGRAM_CHAT_ID'])
    if platform in ('both','discord'):
        send_discord(message, cfg.get('DISCORD_WEBHOOK'))
