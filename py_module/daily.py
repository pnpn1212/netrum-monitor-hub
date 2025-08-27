from py_module.balances import get_balances, get_eth_price_usd
from py_module.config import cfg, tz
from py_module.notification import send_all
from datetime import datetime
from py_module.language import translations, get_lang
from wcwidth import wcswidth

def send_daily_report():
    eth, npt = get_balances(cfg['WALLET_ADDRESS'])
    now = datetime.now(tz).strftime("%H:%M:%S - %d/%m/%Y")
    eth_price = get_eth_price_usd() or 0.0

    lang = get_lang()
    t_dict = translations.get(lang, translations["en"])

    labels = [
        t_dict['time'],
        t_dict['wallet_daily'],
        'ETH',
        'NPT'
    ]
    max_label_len = max(wcswidth(label) for label in labels)

    eth_str = f"{eth:.6f} = ${eth*eth_price:.2f}"
    npt_str = f"{npt:.6f}"

    msg = (
        f"<b>📅 {t_dict['wallet_info']}</b>\n"
        "<pre>"
        f"⏰ {t_dict['time']:<{max_label_len}} | {now}\n"
        f"💳 {t_dict['wallet_daily']:<{max_label_len}} | {cfg['WALLET_ADDRESS']}\n"
        f"💵 {'ETH':<{max_label_len}} | {eth_str}\n"
        f"💰 {'NPT':<{max_label_len}} | {npt_str}\n"
        "</pre>"
    )

    send_all(msg, cfg, platform='both')
