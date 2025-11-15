#!/usr/bin/env python3
import subprocess, pty, os, re, html, time
from datetime import datetime, timezone
from py_module.config import CLAIM_JS, NETRUM_NODE_DIR, cfg, DAILY_STATS, tz
from py_module.utils import countdown
from py_module.daily import send_daily_report
from py_module.notification import send_all
from py_module.balances import get_balances, get_eth_price_usd
from py_module.language import translations, get_lang
from wcwidth import wcswidth

def run_auto_claim():
    max_retries = 12
    retry_interval = 5 * 60
    retries = 0

    while retries <= max_retries:
        claimed_success = False
        output_lines = []

        try:
            master_fd, slave_fd = pty.openpty()
            proc = subprocess.Popen(
                ['node', str(CLAIM_JS)],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
                cwd=NETRUM_NODE_DIR
            )
            os.close(slave_fd)

            while True:
                try:
                    data = os.read(master_fd, 1024).decode('utf-8', errors='ignore')
                    if not data:
                        break
                    for line in data.splitlines():
                        line_clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', line)
                        line_clean = line_clean.replace('[28G', '').strip()
                        if not line_clean:
                            continue

                        print(f"[CLAIM] {line_clean}", flush=True)
                        output_lines.append(line_clean)
                       
                        if re.search(r'\(y/n\)', line_clean, re.IGNORECASE):
                            os.write(master_fd, b'y\n')

                except OSError:
                    break

            os.close(master_fd)
           
            addr = claimable = fee = balance = tx_link = ""
            for line in output_lines:
                if "Mining Address:" in line:
                    addr = line.split("Mining Address:")[-1].strip()
                elif "Claimable Tokens:" in line:
                    claimable_str = line.split("Claimable Tokens:")[-1].strip()
                elif "Required Fee:" in line:
                    fee_str = line.split("Required Fee:")[-1].strip()
                elif "Your Balance:" in line:
                    balance_str = line.split("Your Balance:")[-1].strip()
                elif "Transaction sent:" in line:
                    tx_link = line.split("Transaction sent:")[-1].strip()
            
            claimable = float(claimable_str.split()[0])
            balance = float(balance_str.split()[0])
            fee = float(fee_str.split()[0])
            eth_price = get_eth_price_usd() or 0.0
           
            full_output = '\n'.join(output_lines)
            tx_match = re.search(r'https://basescan\.org/tx/\S+', full_output)
            tx_link = tx_match.group(0) if tx_match else tx_link or 'Link not found'
            
            if "Tokens successfully claimed" in full_output:
                claimed_success = True
                DAILY_STATS['claims'] += 1

                lang = get_lang()
                t = translations.get(lang, translations["en"])

                labels = [
                    f"🫱 {t['address_claim']}",
                    f"💎 {t['claimable']}",
                    f"⛽ {t['fee_claim']}",
                    f"💰 {t['balance']}",
                    f"🔁 {t['status_claim']}",
                    f"🔍 {t['transaction']}"
                ]

                values = [
                    addr,
                    f"{claimable:.4f}",
                    f"{fee:.4f} = ${fee*eth_price:.2f}",
                    f"{balance:.4f} = ${balance*eth_price:.2f}",
                    "✅ Success",
                    tx_link
                ]

                max_label_len = max(wcswidth(label) for label in labels)
                max_value_len = max(len(v) for v in values)

                tele_msg = (
                    f"<b>📥 {t['claim_result']}</b>\n"
                    "<pre>"
                    f"{labels[0]:<{max_label_len}} | {values[0]:<{max_value_len}}\n"
                    f"{labels[1]:<{max_label_len}} | {values[1]:<{max_value_len}}\n"
                    f"{labels[2]:<{max_label_len}} | {values[2]:<{max_value_len}}\n"
                    f"{labels[3]:<{max_label_len}} | {values[3]:<{max_value_len}}\n"
                    f"{labels[4]:<{max_label_len}} | {values[4]:<{max_value_len}}\n"
                    f"{labels[5]:<{max_label_len}} | {values[5]:<{max_value_len}}\n"
                    "</pre>"
                )

                discord_msg = (
                    f"<b>**📥 {t['claim_result']}**</b>\n"
                    "<pre>"
                    f"{labels[0]:<{max_label_len}} | {values[0]:<{max_value_len}}\n"
                    f"{labels[1]:<{max_label_len}} | {values[1]:<{max_value_len}}\n"
                    f"{labels[2]:<{max_label_len}} | {values[2]:<{max_value_len}}\n"
                    f"{labels[3]:<{max_label_len}} | {values[3]:<{max_value_len}}\n"
                    f"{labels[4]:<{max_label_len}} | {values[4]:<{max_value_len}}\n"
                    f"{labels[5]:<{max_label_len}} | {values[5]:<{max_value_len}}\n"
                    "</pre>"
                )

                send_all(tele_msg, cfg, platform='telegram')
                send_all(discord_msg, cfg, platform='discord')
                break

            else:
                retries += 1

                labels = [t['status_claim'], t['output']]
                values = [f"❌ Failed (Retry {retries}/{max_retries})", full_output.strip()]

                max_label_len = max(wcswidth(label) for label in labels)
                max_value_len = max(len(v) for v in values)

                fail_msg = (
                    f"<b>🚨 {t['claim_result']}</b>\n"
                    "<pre>"
                    f"{labels[0]:<{max_label_len}} | {values[0]:<{max_value_len}}\n"
                    f"{labels[1]:<{max_label_len}} | {html.escape(values[1]):<{max_value_len}}\n"
                    "</pre>"
                )
                send_all(fail_msg, cfg, platform='both')

                if retries > max_retries:
                    break

                countdown(retry_interval)

        except Exception as e:
            retries += 1

            if not claimed_success:
                print('[Claim error]', e)

                labels = [t['claim_exception']]
                values = ["\n".join(output_lines)]

                max_label_len = max(wcswidth(label) for label in labels)
                max_value_len = max(len(v) for v in values)

                exc_msg = (
                    f"<b>❌ {t['claim_exception']}</b> (Retry {retries}/{max_retries})\n"
                    "<pre>"
                    f"{labels[0]:<{max_label_len}} | {html.escape(values[0]):<{max_value_len}}\n"
                    "</pre>"
                )
                send_all(exc_msg, cfg, platform='both')

            if retries > max_retries:
                break

            countdown(retry_interval)
