# AI Stock Bot V3 — Gmail OAuth

# 🤖 AI Stock Bot – Automatic Stock Market Monitor

An automated Python-based stock monitoring system that tracks selected Indian stocks during market hours and sends email alerts when predefined monitoring conditions are detected.

The project combines real-time market data, automated monitoring, Gmail OAuth authentication, email notifications, a Streamlit web interface, and Windows Task Scheduler to create a complete automated stock-alert system.

---
📌 **Project Overview**

The **AI Stock Bot** is designed to reduce the need for manually monitoring stock prices throughout the trading day.

The system continuously checks selected Indian stocks during market hours and evaluates predefined conditions.

When an alert condition is detected, the system automatically sends an email notification to the configured recipients through the **Gmail API using OAuth 2.0 authentication**.

### Example monitored Stocks

- RELIANCE.NS
- TCS.NS
- INFY.NS

The monitoring process can run automatically during:

**Monday – Friday  
9:30 AM – 3:00 PM IST**

The monitoring interval can be configured according to the project requirements.

---

# 🚀 Key Features

### 📊 Real-Time Stock Monitoring

The bot monitors selected Indian stock symbols and retrieves their latest market values.

### ⏰ Automated Monitoring

The monitoring process can run automatically at regular intervals during Indian stock-market hours.

### 🔔 Automatic Email Alerts

When a predefined condition is detected, the system sends an email notification automatically.

### 🔐 Gmail OAuth Authentication

The project uses Gmail OAuth authentication instead of storing a Gmail password.

### 🌐 Streamlit Web Interface

A web-based dashboard can be used to view the monitoring system and its status.

### 🖥️ Windows Background Execution

Windows Task Scheduler can be used to start the monitoring bot automatically without manually opening Command Prompt every day.

### 📝 Monitoring Logs

The application displays monitoring activity such as:

- Current time
- Market status
- Stock values
- Monitoring results
- Alert conditions
- Next monitoring interval

### 🔄 Continuous Monitoring

The bot repeatedly checks the market during the configured monitoring period.

---

# 🏗️ System Architecture

```text
                 ┌─────────────────────┐
                 │   Indian Stock      │
                 │    Market Data      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Python Stock      │
                 │     Monitor         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Condition / Alert   │
                 │      Detection      │
                 └──────────┬──────────┘
                            │
                    Condition Triggered?
                       /             \
                     YES              NO
                      │                │
                      ▼                ▼
             ┌───────────────┐   ┌─────────────┐
             │ Gmail API     │   │ Continue    │
             │ OAuth 2.0     │   │ Monitoring  │
             └───────┬───────┘   └──────┬──────┘
                     │                  │
                     ▼                  │
             ┌───────────────┐          │
             │ Email Alert   │          │
             │ to Recipients │          │
             └───────────────┘          │
                                        │
                         ┌──────────────┘
                         ▼
                  Next Monitoring Check
