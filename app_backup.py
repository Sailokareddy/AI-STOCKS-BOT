import os
import base64
import pickle
from datetime import datetime, time
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

    now = datetime.now()

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

    now = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

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
# PAGE
# ============================================================

st.set_page_config(
    page_title="AI Stock Bot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Stock Bot")
st.caption("NIFTY 50 + SENSEX + User Selected Stocks")


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


# ============================================================
# GMAIL SECTION
# ============================================================

st.header("🔐 Gmail Connection")

recipient = st.text_input(
    "Report recipient email",
    value="ai.lokesh060@gmail.com"
)


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

                send_gmail(
                    st.session_state.gmail_service,
                    recipient,
                    "📊 NIFTY 50 + SENSEX Market Report",
                    html
                )

                st.success(
                    "Market report sent successfully."
                )

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

                    send_gmail(
                        st.session_state.gmail_service,
                        recipient,
                        "🚨 Market Movement Alert",
                        alert_html
                    )

                    st.success(
                        "🚨 Alert email sent."
                    )

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