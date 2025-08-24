#!/usr/bin/env python3
from py_module.balances import get_balances, get_eth_price_usd
from py_module.config import cfg, tz
from py_module.notification import send_all
from datetime import datetime

def send_daily_report():
    eth, npt = get_balances(cfg['WALLET_ADDRESS'])
    now = datetime.now(tz).strftime("%H:%M:%S - %d/%m/%Y")
    eth_price = get_eth_price_usd() or 0.0
    msg = (
        "<b>📅 Wallet Check</b>\n"
        "<pre>"
        f"⏰ Time:   {now}\n"
        f"💳 Wallet: {cfg['WALLET_ADDRESS']}\n"
        f"💵 ETH :   {eth:.6f} = ${eth*eth_price:.2f}\n"
        f"💰 NPT :   {npt:.6f}\n"
        "</pre>"
    )
    send_all(msg, cfg, platform='both')
