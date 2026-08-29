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

Check
🔄 How the Project Works

The complete workflow is:

Step 1 – Start the Application

The monitoring application is started manually or automatically through Windows Task Scheduler.

Step 2 – Check Market Hours

The application checks whether the Indian stock market is currently within the configured monitoring period.

Step 3 – Retrieve Stock Data

The application retrieves the latest available values for the configured stock symbols.

Example:

RELIANCE.NS
TCS.NS
INFY.NS
Step 4 – Analyze Stock Movement

The application compares the retrieved values against the predefined monitoring conditions.

Step 5 – Detect Alert Condition

If the configured condition is satisfied, the system generates an alert.

Step 6 – Send Email

The Gmail API is used to send an email notification to the configured recipients.

Step 7 – Continue Monitoring

If no alert is triggered, the application waits for the configured interval and performs the next check.

🖥️ Web Dashboard

The project includes a Streamlit-based interface.

The dashboard can be used to display information such as:

📈 Market status
📊 Monitored stocks
💰 Latest stock values
🔔 Alert status
⏱️ Last monitoring check
📧 Email notification status
🔄 Monitoring status

Example dashboard concept:

╔══════════════════════════════════════════╗
║          AI STOCK BOT                    ║
║      Automatic Market Monitor             ║
╠══════════════════════════════════════════╣
║                                          ║
║ Market Status:     OPEN                  ║
║ Monitoring:        ACTIVE                ║
║                                          ║
║ RELIANCE.NS        ₹XXXX.XX              ║
║ TCS.NS             ₹XXXX.XX              ║
║ INFY.NS            ₹XXXX.XX              ║
║                                          ║
║ Last Check:        12:04 PM              ║
║ Next Check:        12:09 PM              ║
║                                          ║
║ Alert Status:      No Alert              ║
╚══════════════════════════════════════════╝
📁 Project Structure
AI_Stock_Bot_V3_Gmail_OAuth/
│
├── app.py
├── auto_monitor.py
├── app_backup.py
│
├── app_before_animated_ui.py
├── app_before_ui_repair.py
├── repair_app.py
├── install_animated_stock_ui.py
│
├── Start_AI_Stock_Bot.bat
├── Start_AI_Stock_Auto.bat
│
├── requirements.txt
├── package-lock.json
├── README.md
├── .gitignore
│
└── credentials.json        # NOT upload due to security reason
└── token.pickle            # NOT upload due to security reason

Some files are development, backup, repair, or UI versions created during the development process.

🧩 Main Components
app.py

The main Streamlit application.

It is responsible for the web-based interface and displaying stock-monitoring information.

auto_monitor.py

The background monitoring component.

It is responsible for:

Checking market status
Monitoring configured stocks
Evaluating monitoring conditions
Running periodic checks
Triggering email notifications
Start_AI_Stock_Bot.bat

Windows batch file used to start the application.

It simplifies launching the project without manually typing multiple commands.

Start_AI_Stock_Auto.bat

Used to start the automatic monitoring process.

It can also be integrated with Windows Task Scheduler.

requirements.txt

Contains the Python packages required by the project.

Install them using:

pip install -r requirements.txt
.gitignore

Prevents sensitive and unnecessary files from being uploaded to GitHub.

Sensitive files such as:

credentials.json
token.pickle
__pycache__/
*.pyc
.env

should be excluded from version control.

🛠️ Technologies Used
Technology	Purpose
Python	Core application development
Streamlit	Web dashboard
Gmail API	Sending email notifications
Google OAuth 2.0	Secure Gmail authentication
Stock Market Data API/Library	Retrieving market data
Windows Task Scheduler	Automatic background execution
Batch Scripts	Simplified application startup
Git	Version control
GitHub	Source-code hosting
HTML/CSS/Streamlit UI	Dashboard presentation
📦 Requirements

Before installing the project, make sure you have:

Windows 10/11
Python 3.x
Internet connection
Gmail account
Google Cloud account
Git
Required Python packages
GitHub account (optional, for source-code hosting)
⚙️ Installation
1. Clone the Repository

Open Command Prompt and run:

git clone YOUR_GITHUB_REPOSITORY_URL

Then:

cd AI_Stock_Bot_V3_Gmail_OAuth
2. Check Python Installation

Run:

python --version

You should see something similar to:

Python 3.x.x

If Python is installed correctly, continue to the next step.

3. Create a Virtual Environment

It is recommended to create a virtual environment.

python -m venv venv

Activate it:

venv\Scripts\activate
4. Install Dependencies

Run:

pip install -r requirements.txt
🔐 Gmail OAuth Setup

The application uses Gmail OAuth 2.0 for sending email.

Step 1 – Create a Google Cloud Project

Create a project in Google Cloud Console.

Then enable the required Gmail API.

Step 2 – Configure OAuth Consent

Configure the OAuth consent screen for the application.

Step 3 – Create OAuth Credentials

Create an OAuth client for the application.

Download the credentials file.

The file is generally named:

credentials.json

Place it inside the project directory.

IMPORTANT

Never upload this file to a public GitHub repository.

🔑 First Gmail Authentication

Run the application.

During the first authentication process, the application may open a browser window.

Sign in with the Gmail account that you want the application to use.

Grant the required permissions.

After successful authentication, the application can store the authentication token locally.

Example:

token.pickle

or another locally generated token file depending on the implementation.

IMPORTANT

Never upload authentication tokens to GitHub.

▶️ Running the Web Application

From the project directory:

streamlit run app.py

The Streamlit server will provide a local web address.

Open the displayed address in your browser.

Typical local development address:

http://localhost:8501
▶️ Running the Automatic Monitor

Run:

python auto_monitor.py

The terminal will display monitoring information similar to:

AI STOCK BOT – AUTOMATIC BACKGROUND MONITOR
================================================
Schedule: Monday-Friday, 9:30 AM-3:00 PM IST
Interval: Every 5 minutes
Stocks: RELIANCE.NS, TCS.NS, INFY.NS
================================================

Gmail authentication: OK

Checking market...

RELIANCE: XXXX.XX
TCS: XXXX.XX
INFY: XXXX.XX

No 5-point movement detected.

Next check in 5 minutes.
🖥️ Running Automatically on Windows

The monitoring script can be configured with Windows Task Scheduler.

This allows the application to start automatically without manually opening Command Prompt every morning.

Step 1

Open:

Task Scheduler
Step 2

Create a new task.

Example task name:

AI Stock Bot Automatic Monitor
Step 3

Configure the trigger.

For example:

Monday – Friday
Start during market hours
Step 4

Configure the action.

Use the actual Python executable installed on your computer.

You can find it using:

where python

Example:

C:\Users\YOUR_NAME\AppData\Local\Python\python.exe

The Python script should point to:

auto_monitor.py

The working directory should point to the project folder.

🔔 Email Alert System

When the monitoring condition is triggered, the application uses Gmail OAuth authentication to send an email.

Example:

Subject:
AI Stock Alert – RELIANCE.NS

Stock:
RELIANCE.NS

Current Value:
₹XXXX.XX

Alert:
Configured monitoring condition detected.

The recipients can be configured according to the application settings.

🎯 Monitoring Logic

The bot is designed around predefined monitoring conditions.

For example:

Market Open
      ↓
Retrieve Stock Data
      ↓
Check Movement
      ↓
Condition Met?
    /       \
  YES        NO
   ↓          ↓
Send Email   Wait
   ↓          ↓
Continue Monitoring

The exact alert threshold and monitoring logic can be modified inside the Python application.

🔒 Security

Security is an important part of this project.

The following files should never be committed to a public repository:

credentials.json
token.pickle
.env
API keys
OAuth access tokens
OAuth refresh tokens
Passwords
Private keys

Add them to .gitignore.

Example:

credentials.json
token.pickle
*.pickle
.env
__pycache__/
*.pyc
🚨 If Credentials Were Accidentally Uploaded

If an OAuth token, credentials file, API key, or other secret has already been pushed to GitHub:

Revoke/rotate the exposed credential.
Remove the secret from the repository.
Generate a new credential.
Update the local application.
Verify that the old credential can no longer be used.

Simply deleting the file in a new commit does not necessarily remove the secret from Git history.

🧪 Testing

Before enabling automatic background execution, test the application manually.

Test the Python environment
python --version
Test dependencies
pip install -r requirements.txt
Test the web application
streamlit run app.py
Test the monitor
python auto_monitor.py
Test Gmail authentication

Verify that:

Gmail authentication: OK

appears before relying on automatic email alerts.

🛠️ Troubleshooting
Python is not recognized

Try:

where python

If Python is installed but not found, verify that Python is correctly added to PATH.

Streamlit is not recognized

Try:

python -m streamlit run app.py
Gmail authentication fails

Check:

Gmail account
Google Cloud project
Gmail API
OAuth configuration
credentials.json
Internet connection
OAuth permissions
Emails are not being sent

Check:

Gmail OAuth authentication
Recipient addresses
Gmail API configuration
Alert condition
Application logs
Internet connection
Task Scheduler does not start the bot

Check:

Python executable path
auto_monitor.py path
"Start in" directory
Task Scheduler permissions
Trigger configuration
Task history
📈 Future Improvements

Possible future improvements include:

📱 Mobile notifications
📲 WhatsApp notifications
📊 Advanced technical indicators
📈 Interactive stock charts
🤖 AI-based market analysis
🧠 Machine-learning-based prediction
☁️ Cloud deployment
🗄️ Database integration
👥 Multi-user support
🔐 Improved secrets management
📧 HTML email templates
📊 Historical performance analytics
⚠️ Disclaimer

This project is developed for educational and software-development purposes.

The alerts generated by this application should not be considered financial advice.

Stock prices are volatile and market conditions can change rapidly.

Users should perform their own research before making any investment or trading decision.

👨‍💻 Project Purpose

This project demonstrates how Python, APIs, OAuth authentication, automation, web technologies, and operating-system scheduling can be combined to build a practical automated monitoring application.

The project provides hands-on experience with:

Python automation
API integration
OAuth authentication
Email automation
Real-time data processing
Streamlit application development
Background task execution
Windows Task Scheduler
Git and GitHub
Application security
⭐ Project Highlights
                 AI STOCK BOT
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
   Market Data     Monitoring      Dashboard
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                Alert Detection
                      │
                      ▼
                 Gmail OAuth
                      │
                      ▼
                 Email Alert
Built with:

Python • Streamlit • Gmail API • OAuth 2.0 • Stock Market Data • Windows Task Scheduler • Git • GitHub

📄 License

This project can be distributed under the license specified in this repository.

If no license has been added yet, choose an appropriate open-source license before presenting the repository as an open-source project.

⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.


### One important correction before you publish

Your repository currently appears to contain files such as **`credentials.json` and `token.pickle`** from the screenshots you showed earlier. **Do not publish those files in a public repository.** Your previous GitHub screenshot specifically showed GitHub detecting a Google OAuth secret.

For a professional GitHub project, your repository should look more like:

```text
AI-STOCKS-BOT/
│
├── app.py
├── auto_monitor.py
├── requirements.txt
├── README.md
├── .gitignore
├── Start_AI_Stock_Bot.bat
└── Start_AI_Stock_Auto.bat
