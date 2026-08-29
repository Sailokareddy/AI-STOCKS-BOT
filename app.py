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
.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(0,210,255,.13), transparent 26%),
        radial-gradient(circle at 85% 18%, rgba(120,70,255,.14), transparent 28%),
        linear-gradient(135deg,#030712 0%,#07111f 48%,#02050b 100%);
    overflow-x:hidden;
}
.stApp:before {
    content:"";
    position:fixed;
    inset:0;
    pointer-events:none;
    background:
        linear-gradient(rgba(80,170,255,.035) 1px,transparent 1px),
        linear-gradient(90deg,rgba(80,170,255,.035) 1px,transparent 1px);
    background-size:42px 42px;
    animation:gridMove 12s linear infinite;
    z-index:0;
}
@keyframes gridMove { from{transform:translate3d(0,0,0)} to{transform:translate3d(42px,42px,0)} }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
@keyframes pulseGlow { 0%,100%{box-shadow:0 0 18px rgba(0,210,255,.10)} 50%{box-shadow:0 0 42px rgba(0,210,255,.30)} }
@keyframes scan { 0%{transform:translateY(-120%);opacity:0} 15%{opacity:.65} 85%{opacity:.65} 100%{transform:translateY(120%);opacity:0} }
@keyframes ticker { from{transform:translateX(0)} to{transform:translateX(-50%)} }
@keyframes barUp { from{transform:scaleY(.15)} to{transform:scaleY(1)} }
@keyframes blink { 0%,45%,100%{opacity:1} 50%,90%{opacity:.35} }
@keyframes titleFlow { to{background-position:250% center} }
@keyframes spin { to{transform:rotate(360deg)} }

.ai-market-hero {
    position:relative;
    z-index:1;
    overflow:hidden;
    margin:10px 0 24px;
    padding:32px;
    border:1px solid rgba(91,190,255,.28);
    border-radius:28px;
    background:
        radial-gradient(circle at 78% 35%,rgba(0,220,255,.12),transparent 25%),
        linear-gradient(135deg,rgba(10,25,48,.94),rgba(4,9,20,.97));
    animation:pulseGlow 4s ease-in-out infinite;
}
.ai-market-hero:after {
    content:"";
    position:absolute;
    left:0;
    right:0;
    height:2px;
    top:0;
    background:linear-gradient(90deg,transparent,#00d9ff,#8c6cff,transparent);
    animation:scan 5s linear infinite;
}
.ai-kicker {
    color:#51d9ff;
    font-size:.78rem;
    letter-spacing:.25em;
    font-weight:700;
    text-transform:uppercase;
}
.ai-title {
    margin:7px 0;
    font-size:3rem;
    font-weight:900;
    letter-spacing:-.04em;
    background:linear-gradient(90deg,#fff,#70dcff,#a98cff,#fff);
    background-size:250% auto;
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    animation:titleFlow 5s linear infinite;
}
.ai-subtitle { color:#aabbd3; font-size:1rem; }

.stock-ticker-window {
    position:relative;
    z-index:1;
    overflow:hidden;
    margin:0 0 24px;
    padding:12px 0;
    border-top:1px solid rgba(255,255,255,.08);
    border-bottom:1px solid rgba(255,255,255,.08);
    background:rgba(0,0,0,.18);
}
.stock-ticker-track {
    display:flex;
    width:max-content;
    animation:ticker 28s linear infinite;
}
.stock-ticker-item {
    min-width:190px;
    margin-right:12px;
    padding:12px 16px;
    border:1px solid rgba(120,190,255,.14);
    border-radius:14px;
    background:rgba(10,22,40,.72);
}
.stock-name { color:#d9e7f8; font-weight:800; font-size:.92rem; }
.stock-price { color:#fff; font-size:1.15rem; font-weight:800; margin-top:3px; }
.stock-up { color:#36e69a; font-size:.78rem; font-weight:700; }
.stock-live {
    display:inline-block;
    width:7px;
    height:7px;
    margin-right:6px;
    border-radius:50%;
    background:#35e79a;
    box-shadow:0 0 12px #35e79a;
    animation:blink 1.3s infinite;
}
.ai-status {
    position:relative;
    z-index:1;
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    margin-bottom:18px;
}
.ai-status-pill {
    padding:8px 13px;
    border:1px solid rgba(120,190,255,.17);
    border-radius:999px;
    background:rgba(9,20,37,.72);
    color:#a9bdd5;
    font-size:.82rem;
}
.ai-status-pill b { color:#fff; }

.ai-chart-card {
    position:relative;
    z-index:1;
    overflow:hidden;
    min-height:230px;
    margin:0 0 25px;
    padding:22px;
    border:1px solid rgba(95,185,255,.20);
    border-radius:22px;
    background:linear-gradient(145deg,rgba(12,27,49,.88),rgba(5,10,21,.94));
}
.ai-chart-title {
    display:flex;
    justify-content:space-between;
    color:#eaf4ff;
    font-weight:800;
    margin-bottom:12px;
}
.ai-chart {
    height:145px;
    display:flex;
    align-items:flex-end;
    gap:7px;
    padding:12px 5px 4px;
    border-bottom:1px solid rgba(120,180,255,.18);
    background:repeating-linear-gradient(to top,transparent 0,transparent 35px,rgba(100,180,255,.07) 36px);
}
.ai-bar {
    flex:1;
    min-width:5px;
    height:var(--h);
    border-radius:5px 5px 1px 1px;
    transform-origin:bottom;
    background:linear-gradient(to top,#087dff,#38e4ff);
    box-shadow:0 0 12px rgba(0,190,255,.22);
    animation:barUp 1.4s ease-out both;
}
.ai-signal {
    color:#35e79a;
    font-weight:800;
    animation:blink 1.6s infinite;
}
.ai-orb {
    position:absolute;
    width:210px;
    height:210px;
    right:-60px;
    top:-65px;
    border-radius:50%;
    background:radial-gradient(circle,#55ddff 0%,rgba(40,170,255,.12) 38%,transparent 70%);
    filter:blur(3px);
    animation:float 4s ease-in-out infinite;
}
.ai-orbit {
    position:absolute;
    width:150px;
    height:150px;
    right:-30px;
    top:-35px;
    border:1px solid rgba(100,220,255,.20);
    border-radius:50%;
    animation:spin 8s linear infinite;
}
</style>

<div class="ai-market-hero">
    <div class="ai-orb"></div>
    <div class="ai-orbit"></div>
    <div class="ai-kicker">● LIVE • INDIAN MARKET INTELLIGENCE</div>
    <div class="ai-title">🤖 AI Stock Bot</div>
    <div class="ai-subtitle">Real-time market monitoring • smart alerts • Gmail reports</div>
</div>

<div class="stock-ticker-window">
  <div class="stock-ticker-track">
    <div class="stock-ticker-item"><div class="stock-name"><span class="stock-live"></span>NIFTY 50</div><div class="stock-price">LIVE MARKET</div><div class="stock-up">▲ TRACKING</div></div>
    <div class="stock-ticker-item"><div class="stock-name"><span class="stock-live"></span>SENSEX</div><div class="stock-price">LIVE MARKET</div><div class="stock-up">▲ TRACKING</div></div>
    <div class="stock-ticker-item"><div class="stock-name">RELIANCE</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name">TCS</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name">INFY</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name">HDFCBANK</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name"><span class="stock-live"></span>NIFTY 50</div><div class="stock-price">LIVE MARKET</div><div class="stock-up">▲ TRACKING</div></div>
    <div class="stock-ticker-item"><div class="stock-name"><span class="stock-live"></span>SENSEX</div><div class="stock-price">LIVE MARKET</div><div class="stock-up">▲ TRACKING</div></div>
    <div class="stock-ticker-item"><div class="stock-name">RELIANCE</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name">TCS</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name">INFY</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
    <div class="stock-ticker-item"><div class="stock-name">HDFCBANK</div><div class="stock-price">NSE</div><div class="stock-up">▲ MONITORED</div></div>
  </div>
</div>

<div class="ai-status">
  <div class="ai-status-pill">🟢 <b>LIVE ENGINE</b></div>
  <div class="ai-status-pill">📈 <b>STOCK MONITOR</b></div>
  <div class="ai-status-pill">⚡ <b>5-MIN ALERTS</b></div>
  <div class="ai-status-pill">✉️ <b>GMAIL READY</b></div>
</div>

<div class="ai-chart-card">
  <div class="ai-chart-title">
    <span>📈 MARKET ACTIVITY</span>
    <span class="ai-signal">● SCANNING</span>
  </div>
  <div class="ai-chart">
    <i class="ai-bar" style="--h:42%;animation-delay:.02s"></i>
    <i class="ai-bar" style="--h:55%;animation-delay:.08s"></i>
    <i class="ai-bar" style="--h:38%;animation-delay:.14s"></i>
    <i class="ai-bar" style="--h:68%;animation-delay:.20s"></i>
    <i class="ai-bar" style="--h:51%;animation-delay:.26s"></i>
    <i class="ai-bar" style="--h:77%;animation-delay:.32s"></i>
    <i class="ai-bar" style="--h:61%;animation-delay:.38s"></i>
    <i class="ai-bar" style="--h:86%;animation-delay:.44s"></i>
    <i class="ai-bar" style="--h:69%;animation-delay:.50s"></i>
    <i class="ai-bar" style="--h:93%;animation-delay:.56s"></i>
    <i class="ai-bar" style="--h:74%;animation-delay:.62s"></i>
    <i class="ai-bar" style="--h:82%;animation-delay:.68s"></i>
    <i class="ai-bar" style="--h:58%;animation-delay:.74s"></i>
    <i class="ai-bar" style="--h:72%;animation-delay:.80s"></i>
    <i class="ai-bar" style="--h:88%;animation-delay:.86s"></i>
    <i class="ai-bar" style="--h:65%;animation-delay:.92s"></i>
  </div>
</div>
""", unsafe_allow_html=True)

# PAGE
# ============================================================

st.set_page_config(
    page_title="AI Stock Bot",
    page_icon="📈",
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