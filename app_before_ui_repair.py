import os
import base64
import pickle
from datetime import datetime, time
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText

import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# ============================================================
# SETTINGS
# ============================================================

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"

MARKET_TZ = ZoneInfo("Asia/Kolkata")
MARKET_START = time(9, 30)
MARKET_END = time(15, 0)

CHECK_INTERVAL_MS = 5 * 60 * 1000

POINT_STEP = 5


# ============================================================
# GMAIL
# ============================================================

def gmail_auth():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:

        if not os.path.exists(CREDENTIALS_FILE):
            st.error(
                "credentials.json was not found in the same folder as app.py."
            )
            return None

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def send_gmail(service, recipient, subject, html):

    msg = MIMEText(html, "html")

    msg["To"] = recipient
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(
        msg.as_bytes()
    ).decode()

    return service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()


# ============================================================
# MARKET DATA
# ============================================================

def get_price(symbol):

    try:
        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="1d",
            interval="5m",
            auto_adjust=False
        )

        if data.empty:
            return None

        data = data.dropna(subset=["Close"])

        if data.empty:
            return None

        return float(data["Close"].iloc[-1])

    except Exception:
        return None


def get_market_data():

    nifty = get_price("^NSEI")
    sensex = get_price("^BSESN")

    return nifty, sensex


def get_stock_name(symbol):

    if symbol == "^NSEI":
        return "NIFTY 50"

    if symbol == "^BSESN":
        return "SENSEX"

    return symbol.replace(".NS", "").replace(".BO", "")


# ============================================================
# MARKET HOURS
# ============================================================

def market_is_open():

    now = datetime.now(MARKET_TZ)

    current_time = now.time()

    return MARKET_START <= current_time <= MARKET_END


# ============================================================
# 5-POINT MOVEMENT
# ============================================================

def get_price_band(price):

    return int(price // POINT_STEP)


def check_movement(symbol, price):

    if price is None:
        return None

    current_band = get_price_band(price)

    previous_band = st.session_state.price_bands.get(symbol)

    # First price:
    # store it but don't send an alert immediately.
    if previous_band is None:

        st.session_state.price_bands[symbol] = current_band

        return None

    if current_band == previous_band:
        return None

    st.session_state.price_bands[symbol] = current_band

    difference = current_band - previous_band

    if difference > 0:
        direction = "UP"
    else:
        direction = "DOWN"

    points = abs(difference * POINT_STEP)

    return direction, points


# ============================================================
# EMAIL REPORT
# ============================================================

def create_report_html(nifty, sensex, stocks):

    now = datetime.now(MARKET_TZ).strftime("%d-%m-%Y %I:%M:%S %p IST")

    html = f"""
    <html>

    <body style="font-family:Arial;background:#f5f5f5;padding:20px;">

        <div style="
            max-width:700px;
            margin:auto;
            background:white;
            padding:25px;
            border-radius:12px;
        ">

        <h1>🤖 AI Stock Bot</h1>

        <p>
            <b>Indian Market Report</b>
        </p>

        <p>
            Generated: {now}
        </p>

        <hr>

        <h2>📊 Market Indices</h2>

        <table border="1"
               cellpadding="10"
               cellspacing="0"
               style="border-collapse:collapse;width:100%;">

            <tr>
                <th>Index</th>
                <th>Price</th>
            </tr>

            <tr>
                <td>NIFTY 50</td>
                <td>{nifty:,.2f}</td>
            </tr>

            <tr>
                <td>SENSEX</td>
                <td>{sensex:,.2f}</td>
            </tr>

        </table>
    """

    if stocks:

        html += """
        <hr>

        <h2>📌 Selected Stocks</h2>

        <table border="1"
               cellpadding="10"
               cellspacing="0"
               style="border-collapse:collapse;width:100%;">

            <tr>
                <th>Stock</th>
                <th>Price</th>
            </tr>
        """

        for symbol, price in stocks:

            if price is not None:

                html += f"""
                <tr>
                    <td>{get_stock_name(symbol)}</td>
                    <td>{price:,.2f}</td>
                </tr>
                """

        html += "</table>"

    html += """

        <hr>

        <p>
            🤖 AI Stock Bot automatically checks the market
            every 5 minutes during market hours.
        </p>

        <p>
            Market monitoring:
            <b>9:30 AM - 3:00 PM IST</b>
        </p>

        </div>

    </body>

    </html>
    """

    return html


# ============================================================
# EMAIL RECIPIENTS
# ============================================================

def parse_recipients(raw_text):
    """Accept one or many email addresses separated by commas/new lines."""
    recipients = []
    for part in raw_text.replace(",", "\n").splitlines():
        email = part.strip()
        if email and email not in recipients:
            recipients.append(email)
    return recipients


def send_to_all_recipients(service, recipients, subject, html):
    """Send the same message to every configured recipient."""
    sent = 0
    for email in recipients:
        send_gmail(service, email, subject, html)
        sent += 1
    return sent


# ============================================================
# 3D ROBOT / UI
# ============================================================

st.markdown("""
<style>
/* ---------- App background ---------- */
.stApp {
    background:
        radial-gradient(circle at 15% 5%, rgba(55, 140, 255, .12), transparent 28%),
        radial-gradient(circle at 90% 12%, rgba(160, 70, 255, .12), transparent 30%),
        linear-gradient(145deg, #070a12 0%, #0b1020 48%, #070a12 100%);
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* ---------- Hero ---------- */
.ai-hero {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(130, 180, 255, .18);
    border-radius: 28px;
    padding: 28px 30px;
    margin-bottom: 20px;
    background: linear-gradient(135deg, rgba(24,32,58,.96), rgba(11,16,30,.92));
    box-shadow: 0 24px 70px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.06);
}
.ai-hero:after {
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    right: -90px;
    top: -110px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(88,166,255,.22), transparent 68%);
}
.ai-kicker {
    color: #78b7ff;
    font-size: .82rem;
    letter-spacing: .18em;
    text-transform: uppercase;
    font-weight: 700;
}
.ai-title {
    font-size: clamp(2rem, 5vw, 3.6rem);
    font-weight: 900;
    line-height: 1;
    margin: 8px 0;
    color: #f5f8ff;
}
.ai-subtitle {
    color: #aeb9cc;
    font-size: 1rem;
}

/* ---------- CSS 3D robot ---------- */
.robot-scene {
    position: absolute;
    right: 34px;
    top: 12px;
    width: 190px;
    height: 170px;
    perspective: 700px;
    pointer-events: none;
}
.robot {
    position: relative;
    width: 120px;
    height: 140px;
    margin: 12px auto 0;
    transform-style: preserve-3d;
    animation: robotFloat 3.4s ease-in-out infinite;
}
.robot-head {
    position: absolute;
    left: 25px;
    top: 0;
    width: 70px;
    height: 58px;
    border-radius: 18px;
    background: linear-gradient(145deg, #dceaff, #6b88ad);
    box-shadow: inset -7px -7px 12px rgba(0,0,0,.28), 0 12px 28px rgba(75,150,255,.28);
    transform: rotateX(7deg) rotateY(-12deg);
}
.robot-face {
    position: absolute;
    left: 10px;
    top: 13px;
    width: 50px;
    height: 30px;
    border-radius: 11px;
    background: #07101c;
    box-shadow: inset 0 0 16px rgba(74,184,255,.35);
}
.robot-eye {
    position: absolute;
    top: 9px;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #69e7ff;
    box-shadow: 0 0 14px #69e7ff;
    animation: blink 4s infinite;
}
.robot-eye.left { left: 10px; }
.robot-eye.right { right: 10px; }
.robot-mouth {
    position: absolute;
    left: 18px;
    bottom: 5px;
    width: 14px;
    height: 4px;
    border-radius: 5px;
    background: #69e7ff;
    box-shadow: 0 0 10px #69e7ff;
}
.robot-antenna {
    position: absolute;
    left: 57px;
    top: -17px;
    width: 5px;
    height: 18px;
    background: #8db8e8;
}
.robot-antenna:after {
    content: "";
    position: absolute;
    left: -5px;
    top: -8px;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    background: #68f0b1;
    box-shadow: 0 0 20px rgba(104,240,177,.9);
    animation: pulse 1.5s infinite;
}
.robot-body {
    position: absolute;
    left: 15px;
    top: 66px;
    width: 90px;
    height: 62px;
    border-radius: 20px;
    background: linear-gradient(145deg, #7895ba, #334b6b);
    box-shadow: inset -8px -9px 14px rgba(0,0,0,.28), 0 16px 32px rgba(0,0,0,.35);
    transform: rotateX(8deg) rotateY(-12deg);
}
.robot-panel {
    position: absolute;
    left: 22px;
    top: 13px;
    width: 46px;
    height: 30px;
    border-radius: 9px;
    background: #07101c;
    border: 1px solid rgba(104,231,255,.45);
}
.robot-bar {
    position: absolute;
    left: 8px;
    right: 8px;
    top: 8px;
    height: 4px;
    border-radius: 5px;
    background: #65e8ff;
    box-shadow: 0 0 10px #65e8ff;
}
.robot-bar:nth-child(2) {
    top: 17px;
    width: 26px;
    background: #68f0b1;
    box-shadow: 0 0 10px #68f0b1;
}
.robot-arm {
    position: absolute;
    top: 74px;
    width: 17px;
    height: 50px;
    border-radius: 10px;
    background: linear-gradient(145deg, #829fc4, #344b68);
}
.robot-arm.left { left: -1px; transform: rotate(16deg); }
.robot-arm.right { right: -1px; transform: rotate(-16deg); }

@keyframes robotFloat {
    0%,100% { transform: translateY(0) rotateY(-7deg); }
    50% { transform: translateY(-10px) rotateY(7deg); }
}
@keyframes pulse {
    0%,100% { transform: scale(.85); opacity:.7; }
    50% { transform: scale(1.12); opacity:1; }
}
@keyframes blink {
    0%, 94%, 100% { transform: scaleY(1); }
    96% { transform: scaleY(.08); }
}

/* ---------- Cards ---------- */
.section-card {
    border: 1px solid rgba(160,185,220,.12);
    border-radius: 22px;
    padding: 20px;
    background: rgba(17,23,39,.72);
    box-shadow: 0 14px 45px rgba(0,0,0,.22);
    margin: 12px 0;
}
.status-pill {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 999px;
    background: rgba(104,240,177,.11);
    border: 1px solid rgba(104,240,177,.28);
    color: #79f0b8;
    font-weight: 700;
    font-size: .82rem;
}
.small-note {
    color: #8e9bb1;
    font-size: .86rem;
}
@media (max-width: 800px) {
    .robot-scene { opacity: .25; right: -10px; }
}
</style>

<div class="ai-hero">
  <div class="ai-kicker">REAL-TIME INDIAN MARKET INTELLIGENCE</div>
  <div class="ai-title">🤖 AI Stock Bot</div>
  <div class="ai-subtitle">
    NIFTY 50 • SENSEX • Your Stocks • 5-Minute Alerts • Gmail Reports
  </div>
  <div class="robot-scene">
    <div class="robot">
      <div class="robot-antenna"></div>
      <div class="robot-head">
        <div class="robot-face">
          <div class="robot-eye left"></div>
          <div class="robot-eye right"></div>
          <div class="robot-mouth"></div>
        </div>
      </div>
      <div class="robot-arm left"></div>
      <div class="robot-arm right"></div>
      <div class="robot-body">
        <div class="robot-panel">
          <div class="robot-bar"></div>
          <div class="robot-bar"></div>
        </div>
      </div>
    </div>
  </div>
</div>
"""
st.markdown(helpers, unsafe_allow_html=True)

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="AI Stock Bot",
    page_icon="🤖",
    layout="wide"
)

st.caption("Your personal market-monitoring dashboard")


# ============================================================
# SESSION STATE
# ============================================================

if "gmail_service" not in st.session_state:
    st.session_state.gmail_service = None

if "price_bands" not in st.session_state:
    st.session_state.price_bands = {}

if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

if "last_report" not in st.session_state:
    st.session_state.last_report = None

if "recipients_text" not in st.session_state:
    st.session_state.recipients_text = "ai.lokesh060@gmail.com"


# ============================================================
# DASHBOARD STRIP
# ============================================================

now_ist = datetime.now(MARKET_TZ)
market_open_now = MARKET_START <= now_ist.time() <= MARKET_END

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("🕘 IST Time", now_ist.strftime("%I:%M:%S %p"))
with c2:
    st.metric("📡 Market Window", "OPEN" if market_open_now else "CLOSED")
with c3:
    st.metric("🔄 Check Interval", "5 minutes")


# ============================================================
# GMAIL SECTION
# ============================================================

st.header("🔐 Gmail Connection")

recipient_text = st.text_area(
    "📧 Report recipient email(s)",
    value=st.session_state.recipients_text,
    height=92,
    help="Add one or more email addresses. Use a new line or comma between addresses."
)
st.session_state.recipients_text = recipient_text
recipients = parse_recipients(recipient_text)

if recipients:
    st.caption(f"📨 {len(recipients)} recipient(s) configured: " + " • ".join(recipients))
else:
    st.warning("Add at least one valid recipient email address.")


if st.button("🔐 Connect Gmail", type="primary"):

    try:

        service = gmail_auth()

        if service:

            st.session_state.gmail_service = service

            st.success("Gmail connected successfully.")

    except Exception as e:

        st.error(f"Gmail connection failed: {e}")


# Automatically load Gmail if token already exists

if st.session_state.gmail_service is None:

    if os.path.exists(TOKEN_FILE):

        try:

            service = gmail_auth()

            if service:

                st.session_state.gmail_service = service

                st.success("Gmail automatically connected.")

        except Exception:
            pass


if st.session_state.gmail_service:

    st.success("Connected.")


# ============================================================
# STOCK SELECTION
# ============================================================

st.divider()

st.header("📌 Select Your Stocks")

st.write(
    "Enter one or more NSE stock symbols. "
    "Example: RELIANCE.NS"
)

stock_text = st.text_area(
    "Your selected stocks",
    value="RELIANCE.NS\nTCS.NS\nINFY.NS",
    height=150
)

selected_symbols = []

for line in stock_text.splitlines():

    symbol = line.strip().upper()

    if symbol:
        selected_symbols.append(symbol)


st.write("Selected stocks:")
st.caption("👤 These are completely user-controlled. Add as many NSE symbols as you need.")

if selected_symbols:

    for symbol in selected_symbols:
        st.write(f"• {symbol}")

else:

    st.info("No additional stocks selected.")


# ============================================================
# MANUAL REPORT
# ============================================================

st.divider()

st.header("📩 Send Market Report")

if st.button("📩 Send NIFTY 50 + SENSEX Report"):

    try:

        if not st.session_state.gmail_service:

            st.error(
                "Please connect Gmail first."
            )

        else:

            nifty, sensex = get_market_data()

            stock_data = []

            for symbol in selected_symbols:

                price = get_price(symbol)

                stock_data.append(
                    (symbol, price)
                )

            if nifty is None or sensex is None:

                st.error(
                    "Unable to get NIFTY/SENSEX data."
                )

            else:

                html = create_report_html(
                    nifty,
                    sensex,
                    stock_data
                )

                if not recipients:
                    st.error("Please add at least one recipient email.")
                else:
                    sent = send_to_all_recipients(
                        st.session_state.gmail_service,
                        recipients,
                        "📊 NIFTY 50 + SENSEX Market Report",
                        html
                    )
                    st.success(f"Market report sent successfully to {sent} recipient(s).")

    except Exception as e:

        st.error(
            f"Report sending failed: {e}"
        )


# ============================================================
# AUTOMATIC MONITORING
# ============================================================

st.divider()

st.header("⏱️ Automatic 5-Minute Monitoring")

st.write(
    "The bot checks NIFTY 50, SENSEX and your selected "
    "stocks every 5 minutes."
)

st.info(
    "Automatic monitoring works only between "
    "9:30 AM and 3:00 PM IST."
)


# Start / Stop

if st.button("▶️ Start Automatic Monitoring"):

    st.session_state.monitoring = True

    st.success(
        "Automatic monitoring started."
    )


if st.button("⏹️ Stop Automatic Monitoring"):

    st.session_state.monitoring = False

    st.warning(
        "Automatic monitoring stopped."
    )


if st.session_state.monitoring:

    st.success(
        "🟢 Monitoring is ACTIVE"
    )

    # Refresh Streamlit every 5 minutes
    st_autorefresh(
        interval=CHECK_INTERVAL_MS,
        key="market_monitor"
    )


# ============================================================
# AUTOMATIC CHECK
# ============================================================

if st.session_state.monitoring:

    if market_is_open():

        nifty, sensex = get_market_data()

        stock_data = []

        for symbol in selected_symbols:

            price = get_price(symbol)

            stock_data.append(
                (symbol, price)
            )


        # ----------------------------------------------------
        # SHOW CURRENT PRICES
        # ----------------------------------------------------

        st.divider()

        st.header("📈 Live Market Status")

        col1, col2 = st.columns(2)

        with col1:

            if nifty is not None:

                st.metric(
                    "NIFTY 50",
                    f"{nifty:,.2f}"
                )

            else:

                st.error(
                    "NIFTY data unavailable"
                )


        with col2:

            if sensex is not None:

                st.metric(
                    "SENSEX",
                    f"{sensex:,.2f}"
                )

            else:

                st.error(
                    "SENSEX data unavailable"
                )


        # ----------------------------------------------------
        # DETECT 5 POINT MOVEMENT
        # ----------------------------------------------------

        alerts = []


        nifty_alert = check_movement(
            "^NSEI",
            nifty
        )

        if nifty_alert:

            direction, points = nifty_alert

            alerts.append(
                (
                    "NIFTY 50",
                    nifty,
                    direction,
                    points
                )
            )


        sensex_alert = check_movement(
            "^BSESN",
            sensex
        )

        if sensex_alert:

            direction, points = sensex_alert

            alerts.append(
                (
                    "SENSEX",
                    sensex,
                    direction,
                    points
                )
            )


        # Selected stocks

        for symbol, price in stock_data:

            alert = check_movement(
                symbol,
                price
            )

            if alert:

                direction, points = alert

                alerts.append(
                    (
                        get_stock_name(symbol),
                        price,
                        direction,
                        points
                    )
                )


        # ----------------------------------------------------
        # SEND ALERT EMAIL
        # ----------------------------------------------------

        if alerts:

            if st.session_state.gmail_service:

                alert_html = f"""
                <html>

                <body style="font-family:Arial;">

                <h1>🚨 AI Stock Bot Alert</h1>

                <p>
                Market movement detected.
                </p>

                <table border="1"
                       cellpadding="10"
                       cellspacing="0">

                <tr>
                    <th>Stock / Index</th>
                    <th>Price</th>
                    <th>Direction</th>
                    <th>Movement</th>
                </tr>
                """


                for name, price, direction, points in alerts:

                    emoji = "🟢" if direction == "UP" else "🔴"

                    alert_html += f"""
                    <tr>

                        <td>{name}</td>

                        <td>{price:,.2f}</td>

                        <td>
                            {emoji} {direction}
                        </td>

                        <td>
                            {points} points
                        </td>

                    </tr>
                    """


                alert_html += """
                </table>

                <br>

                <p>
                🤖 AI Stock Bot
                </p>

                </body>

                </html>
                """


                try:

                    if not recipients:
                        st.error("Please add at least one recipient email.")
                    else:
                        sent = send_to_all_recipients(
                            st.session_state.gmail_service,
                            recipients,
                            "🚨 Market Movement Alert",
                            alert_html
                        )
                        st.success(f"🚨 Alert email sent to {sent} recipient(s).")

                except Exception as e:

                    st.error(
                        f"Alert email failed: {e}"
                    )

            else:

                st.warning(
                    "Gmail is not connected."
                )


        st.caption(
            "Next automatic check: approximately 5 minutes."
        )


    else:

        st.warning(
            "⏸️ Market is currently closed. "
            "Automatic monitoring will operate only "
            "from 9:30 AM to 3:00 PM IST."
        )