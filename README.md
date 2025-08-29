#### *Please select other languages:*
[![English](https://raw.githubusercontent.com/gosquared/flags/master/flags/flags/shiny/24/United-States.png)](README.md)
[![Việt Nam](https://raw.githubusercontent.com/gosquared/flags/master/flags/flags/shiny/24/Vietnam.png)](README.vn.md)   

------
# Netrum Monitor Automatic

A tool to manage and monitor your Netrum Lite Node directly via Telegram and Discord Webhooks.

## ✨ Features
- Check node online/offline status  
- Monitor wallet balance & address 
- Set a delay before executing an action
- Claim mining rewards   
- View bot logs
- Change language EN/VN

## 📦 Requirements
- Docker Compose
- TELEGRAM_CHAT_ID & TELEGRAM_BOT_TOKEN
- DISCORD_WEBHOOK (optional) 
- Netrum Lite Node installed and running
- Linux environment (VPS, WSL on Windows, or Hyper-V)

## 📁 Folder Structure
```
netrum-monitor-hub/
├─ py_module
    ├─ 
├─ .netrum
├─ docker-compose.yml
├─ Dockerfile
└─ netrum_main.py
```

## ⚙️ Setup
✅ Telegram Bot Token
- Create via [@BotFather](https://t.me/BotFather)
- Save the token (e.g., 123456789:ABCDEF...)

✅ Telegram Chat ID
- Send a message to your bot
- Use [@RawDataBot](https://t.me/RawDataBot) or
```bash
https://api.telegram.org/bot<your_token>/getUpdates
```

> ⚠️ Not supported on PowerShell/CMD. Use WSL or a Linux VPS.

### 1. Install required libraries
```bash
cd $HOME && bash <(curl -s https://raw.githubusercontent.com/vnbnode/binaries/main/docker-install.sh)
```

### 2. Clone this repository
```bash
git clone https://github.com/pnpn1212/netrum-monitor-hub.git
cd netrum-monitor-hub
```

### 3. Configure `.netrum`
Edit a `.netrum` file in your bot directory:
```
nano .netrum
```

```
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Wallet Netrum
WALLET_ADDRESS=

# DISCORD_WEBHOOK (optional)
DISCORD_WEBHOOK=
```  

### 4. Run the bot:
```
docker compose up --build -d
```
---

### Once the bot is online, use slash commands in Telegram:

`/start` → Start Menu Bot  

`/wallet` → View wallet balance and address  

`/status` → Check if node is running  

`/logs` → Check bot logs

`/claim` → To claim the reward, click ✅ Yes or ❌ Cancel

`/set_timeout` → Set a delay before executing an action

`/lang` → Change language EN/VN

## ⬆️ Upgrade
```
cd $HOME/netrum-monitor-hub
git pull
```

---
## 📑 Example Output

<img width="750" height="459" alt="image" src="https://github.com/user-attachments/assets/4c78d9f0-1b85-4118-8b66-1af2b0b8063e" />
<img width="741" height="1280" alt="image" src="https://github.com/user-attachments/assets/6ef52dbe-8c5f-4afe-9ced-f21014e50578" />


