#### *Please select other languages:*
[![English](https://raw.githubusercontent.com/gosquared/flags/master/flags/flags/shiny/24/United-States.png)](README.md)
[![Việt Nam](https://raw.githubusercontent.com/gosquared/flags/master/flags/flags/shiny/24/Vietnam.png)](README.vn.md)   

------
# Netrum Monitor Hub

Công cụ quản lý và giám sát Netrum Lite Node trực tiếp thông qua Telegram và Discord Webhooks.

## ✨ Tính năng
- Kiểm tra trạng thái online/offline của node
- Giám sát số dư ví & địa chỉ
- Đặt thời gian cho mỗi lần gửi báo cáo trạng thái mining
- Claim phần thưởng đào coin
- Xem log của bot

## 📦 Yêu cầu
- Docker Compose
- TELEGRAM_CHAT_ID & TELEGRAM_BOT_TOKEN
- DISCORD_WEBHOOK (tùy chọn) 
- Netrum Lite Node đã được cài và đang chạy
- Môi trường Linux (VPS, WSL trên Windows hoặc Hyper-V)

## 📁 Cấu trúc thư mục
```
netrum-monitor-hub/
├─ py_module
    ├─ balances
    ├─ bot
    ├─ claim
    ├─ config
    ├─ daily
    ├─ discord
    ├─ log
    ├─ monitor
    ├─ notification
    ├─ parse_log
    ├─ status
    ├─ utils
├─ .netrum
├─ docker-compose.yml
├─ Dockerfile
└─ netrum_main.py
```

## ⚙️ Cài đặt
✅ Telegram Bot Token
- Tạo thông qua @BotFather
- Lưu token (ví dụ: 123456789:ABCDEF...)

✅ Telegram Chat ID
- Gửi một tin nhắn tới bot của bạn
- Sử dụng @userinfobot hoặc
```
https://api.telegram.org/bot<your_token>/getUpdates
```

> ⚠️ Không hỗ trợ trên PowerShell/CMD. Vui lòng sử dụng WSL hoặc VPS Linux.

### 1. Cài thư viện cần thiết
```
cd $HOME && bash <(curl -s https://raw.githubusercontent.com/vnbnode/binaries/main/docker-install.sh)
```

### 2. Clone repository này
```
git clone https://github.com/pnpn1212/netrum-monitor-hub.git
cd netrum-monitor-hub
```

### 3. Cấu hình `.netrum`
Chỉnh sửa file `.netrum` trong thư mục bot::

```
# Cấu hình Telegram Bot
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Ví Netrum
WALLET_ADDRESS=

# DISCORD_WEBHOOK (tùy chọn)
DISCORD_WEBHOOK=
```  

### 4. Chạy bot:
```
docker compose up --build -d
```
---

### Khi bot đã online, sử dụng các lệnh slash trong Telegram:

`/start` → Menu khởi động Bot

`/wallet` → Xem số dư và địa chỉ ví

`/status` → Kiểm tra node đang chạy hay không

`/logs` → Xem log của bot

`/claim` → Claim phần thưởng, click ✅ Yes hoặc ❌ Cancel

`/set_timeout` → Đặt thời gian cho mỗi lần gửi báo cáo trạng thái mining

---
## 📑 Ví dụ Output

<img width="750" height="459" alt="image" src="https://github.com/user-attachments/assets/4c78d9f0-1b85-4118-8b66-1af2b0b8063e" />
<img width="741" height="1280" alt="image" src="https://github.com/user-attachments/assets/6ef52dbe-8c5f-4afe-9ced-f21014e50578" />


