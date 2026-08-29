import os, base64, pickle, time as time_module
from datetime import datetime, time
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText

import yfinance as yf
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"
MARKET_TZ = ZoneInfo("Asia/Kolkata")
MARKET_START = time(9, 30)
MARKET_END = time(15, 0)
CHECK_SECONDS = 300
POINT_STEP = 5

RECIPIENTS = ["ai.lokesh060@gmail.com", "dinksh7@gmail.com"]
SELECTED_SYMBOLS = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
price_bands = {}

def gmail_auth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError("credentials.json is missing.")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("gmail", "v1", credentials=creds)

def send_gmail(service, recipient, subject, html):
    msg = MIMEText(html, "html")
    msg["To"] = recipient
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

def get_price(symbol):
    try:
        data = yf.Ticker(symbol).history(
            period="1d", interval="5m", auto_adjust=False
        )
        if data.empty:
            return None
        data = data.dropna(subset=["Close"])
        return float(data["Close"].iloc[-1]) if not data.empty else None
    except Exception as e:
        print(f"[PRICE ERROR] {symbol}: {e}")
        return None

def get_stock_name(symbol):
    if symbol == "^NSEI": return "NIFTY 50"
    if symbol == "^BSESN": return "SENSEX"
    return symbol.replace(".NS", "").replace(".BO", "")

def market_is_open():
    now = datetime.now(MARKET_TZ)
    return now.weekday() < 5 and MARKET_START <= now.time() <= MARKET_END

def check_movement(symbol, price):
    if price is None:
        return None
    current_band = int(price // POINT_STEP)
    previous_band = price_bands.get(symbol)
    if previous_band is None:
        price_bands[symbol] = current_band
        return None
    if current_band == previous_band:
        return None
    price_bands[symbol] = current_band
    difference = current_band - previous_band
    return ("UP" if difference > 0 else "DOWN", abs(difference * POINT_STEP))

def build_alert_html(alerts):
    now = datetime.now(MARKET_TZ).strftime("%d-%m-%Y %I:%M:%S %p IST")
    rows = "".join(
        f"<tr><td style='padding:10px;border:1px solid #ccc'>{name}</td>"
        f"<td style='padding:10px;border:1px solid #ccc'>{price:,.2f}</td>"
        f"<td style='padding:10px;border:1px solid #ccc'>{'🟢' if direction=='UP' else '🔴'} {direction}</td>"
        f"<td style='padding:10px;border:1px solid #ccc'>{points} points</td></tr>"
        for name, price, direction, points in alerts
    )
    return f"""<html><body style="font-family:Arial;background:#f5f5f5;padding:20px">
<div style="max-width:700px;margin:auto;background:white;padding:25px;border-radius:12px">
<h1>🚨 AI Stock Bot Alert</h1><p><b>Market movement detected</b></p>
<p>Time: {now}</p><table style="border-collapse:collapse;width:100%">
<tr><th style="padding:10px;border:1px solid #ccc">Stock / Index</th>
<th style="padding:10px;border:1px solid #ccc">Price</th>
<th style="padding:10px;border:1px solid #ccc">Direction</th>
<th style="padding:10px;border:1px solid #ccc">Movement</th></tr>{rows}
</table><p>🤖 AI Stock Bot — automatic 5-minute monitoring.</p>
</div></body></html>"""

def run_check(service):
    now = datetime.now(MARKET_TZ)
    print("\n" + "="*60)
    print(now.strftime("%d-%m-%Y %I:%M:%S %p IST"))
    print("Checking market...")
    values = [("^NSEI", get_price("^NSEI")), ("^BSESN", get_price("^BSESN"))]
    values += [(s, get_price(s)) for s in SELECTED_SYMBOLS]
    alerts = []
    for symbol, price in values:
        print(f"{get_stock_name(symbol)}: {price}")
        result = check_movement(symbol, price)
        if result:
            direction, points = result
            alerts.append((get_stock_name(symbol), price, direction, points))
    if alerts:
        html = build_alert_html(alerts)
        for email in RECIPIENTS:
            send_gmail(service, email, "🚨 Market Movement Alert", html)
        print(f"ALERT EMAIL SENT to {len(RECIPIENTS)} recipient(s).")
    else:
        print("No 5-point movement detected.")

def main():
    print("="*60)
    print("AI STOCK BOT - AUTOMATIC BACKGROUND MONITOR")
    print("="*60)
    print("Schedule: Monday-Friday, 9:30 AM-3:00 PM IST")
    print("Interval: every 5 minutes")
    print("Recipients:", ", ".join(RECIPIENTS))
    print("Stocks:", ", ".join(SELECTED_SYMBOLS))
    print("="*60)
    try:
        service = gmail_auth()
        print("Gmail authentication: OK")
    except Exception as e:
        print("Gmail authentication FAILED:", e)
        input("Press Enter to close...")
        return

    last_day = None
    while True:
        now = datetime.now(MARKET_TZ)
        if last_day != now.date():
            price_bands.clear()
            last_day = now.date()
        if market_is_open():
            try:
                run_check(service)
            except Exception as e:
                print("CHECK ERROR:", e)
            print("Next check in 5 minutes.")
            time_module.sleep(CHECK_SECONDS)
        else:
            print("Market closed. Waiting...")
            time_module.sleep(60)

if __name__ == "__main__":
    main()
