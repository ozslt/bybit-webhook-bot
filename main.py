from fastapi import FastAPI, Request
import requests, time, hmac, hashlib, json
import os

app = FastAPI()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE = "https://api.bybit.com"  # valós tőzsde Spot API

SYMBOL = "SOLUSDC"   # Spot pár
QTY = 0.05           # fél 0.1 SOL

# --- Aláírás generálása Bybit API-hoz ---
def sign_request(timestamp, body_str=""):
    return hmac.new(
        API_SECRET.encode(),
        (timestamp + API_KEY + body_str).encode(),
        hashlib.sha256
    ).hexdigest()

def bybit_headers(timestamp, body_str):
    return {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-SIGN": sign_request(timestamp, body_str),
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": "5000",
        "Content-Type": "application/json"
    }

# --- Spot megrendelés küldése ---
def send_order(side):
    endpoint = "/v5/order/create"
    timestamp = str(int(time.time() * 1000))

    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "orderType": "Market",
        "qty": str(QTY)
    }

    body_str = json.dumps(body)
    headers = bybit_headers(timestamp, body_str)
    r = requests.post(BASE + endpoint, json=body, headers=headers)

    try:
        return r.json()
    except:
        return {"error": "Cannot decode response", "response_text": r.text}

# --- Webhook endpoint ---
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    action = data.get("action")

    if not action:
        return {"error": "Missing action field"}

    if action.lower() == "buy":
        order = send_order("Buy")
        return {"action": "buy", "order": order}

    elif action.lower() == "sell":
        order = send_order("Sell")
        return {"action": "sell", "order": order}

    else:
        return {"error": "Unknown action"}
