# AI-STOCKS-BOT
AI-powered stock monitoring bot that automatically tracks selected Indian stocks during market hours and sends real-time email alerts using Gmail OAuth.
# 📈 AI Stock Bot – Automatic Market Monitor

An automated Python-based stock monitoring system that tracks selected Indian stocks during market hours and sends email notifications when predefined monitoring conditions are detected.

## 🚀 Features

- 📊 Monitors selected Indian stocks such as Reliance, TCS and Infosys
- ⏰ Automatically runs during Indian stock market hours
- 🔄 Checks stock data at regular intervals
- 📧 Sends alerts through Gmail
- 🔐 Uses Gmail OAuth authentication for secure email access
- 🤖 Runs automatically in the background
- 🖥️ Includes a Streamlit-based interface
- ⚙️ Supports Windows Task Scheduler for automatic startup
- 📝 Includes logging and monitoring functionality

## 🛠️ Technologies Used

- Python
- Streamlit
- Gmail API / OAuth
- Stock market data APIs
- Windows Task Scheduler
- Git & GitHub

## ⚙️ How It Works

1. The application starts automatically through Windows Task Scheduler.
2. The background monitor checks whether the Indian stock market is open.
3. During market hours, the bot monitors the configured stocks at regular intervals.
4. When the configured conditions are detected, the system generates an alert.
5. The alert is sent to the configured email recipients through Gmail.
6. Outside market hours, the bot remains waiting until the next market session.

## 📌 Example Stocks

- RELIANCE.NS
- TCS.NS
- INFY.NS

## 🔒 Security

Sensitive authentication files such as:

- `credentials.json`
- `token.pickle`

are excluded from GitHub using `.gitignore`.

**Never upload API credentials, OAuth secrets, passwords, or tokens to a public repository.**

## 🎯 Project Goal

The goal of this project is to automate stock-market monitoring and notifications so that users don't need to manually check the market or start the monitoring program every time.

## 📂 Project Structure

```text
AI_Stock_Bot/
│
├── app.py
├── auto_monitor.py
├── repair_app.py
├── install_animated_stock_ui.py
├── requirements.txt
├── package-lock.json
├── Start_AI_Stock_Bot.bat
├── Start_AI_Stock_Auto.bat
├── README.md
└── .gitignore
