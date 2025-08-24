#!/usr/bin/env python3
import subprocess, pty, os, re, html, time
from datetime import datetime, timezone
from py_module.config import CLAIM_JS, NETRUM_NODE_DIR, cfg, DAILY_STATS, tz
from py_module.utils import countdown
from py_module.daily import send_daily_report
from py_module.notification import send_all
from py_module.balances import get_balances, get_eth_price_usd

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

                tele_msg = (
                    "<b>📥 Claim Result</b>"
                    "<pre>"
                    f"🫱 Address:     {addr}\n"
                    f"💎 Claimable:   {claimable:.6f}\n"
                    f"⛽ Fee:         {fee:.6f} = ${fee*eth_price:.2f}\n"
                    f"💰 Balance:     {balance:.6f} = ${balance*eth_price:.2f}\n"
                    f"🔁 Status:      ✅ Success\n"
                    f"🔍 Transaction: {tx_link}\n"
                    "</pre>"
                )

                discord_msg = (
                    "<b>**📥 Claim Result**</b>\n"
                    "<pre>"
                    f"🫱 Address:     {addr}\n"
                    f"💎 Claimable:   {claimable:.6f}\n"
                    f"⛽ Fee:         {fee:.6f} = ${fee*eth_price:.2f}\n"
                    f"💰 Balance:     {balance:.6f} = ${balance*eth_price:.2f}\n"
                    f"🔁 Status:      ✅ Success\n"
                    f"🔍 Transaction: {tx_link}\n"
                    "</pre>"
                )

                send_all(tele_msg, cfg, platform='telegram')
                send_all(discord_msg, cfg, platform='discord')
                break

            else:
                retries += 1
                fail_msg = (
                    "<b>🚨 Claim Result</b>\n"
                    f"🔁 Status: ❌ Failed (Retry {retries}/{max_retries})\n"
                    "📦 Output:\n"
                    "<pre>\n" + html.escape(full_output.strip()) + "\n</pre>"
                )
                send_all(fail_msg, cfg, platform='both')
                if retries > max_retries:
                    break
                countdown(retry_interval)

        except Exception as e:
            retries += 1
            if not claimed_success:
                print('[Claim error]', e)
                exc_msg = (
                    f"<b>❌ Claim Exception</b> (Retry {retries}/{max_retries})\n"
                    "<pre>\n" + "\n".join(output_lines) + "\n</pre>"
                )
                send_all(exc_msg, cfg, platform='both')
            if retries > max_retries:
                break
            countdown(retry_interval)
