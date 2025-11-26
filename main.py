from fastapi import FastAPI, Request
import requests, time, hmac, hashlib, json
import os

app = FastAPI()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE = "https://api-testnet.bybit.com"

def sign_request(timestamp, body_str=""):
    return hmac.new(
        API_SECRET.encode(),
        (timestamp + API_KEY + "5000" + body_str).encode(),
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

def send_order(symbol, side, qty):
    endpoint = "/v5/order/create"
    timestamp = str(int(time.time() * 1000))

    body = {
        "category": "linear",
        "symbol": symbol,
        "side": side,
        "orderType": "Market",
        "qty": qty,
        "reduceOnly": False
    }

    body_str = json.dumps(body)
    headers = bybit_headers(timestamp, body_str)

    try:
        r = requests.post(BASE + endpoint, json=body, headers=headers)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    action = data.get("action")
    symbol = data.get("symbol")
    qty = data.get("qty")

    if action and action.lower() == "buy":
        order = send_order(symbol, "Buy", qty)
        return {"order": order}

    return {"message": "No action taken"}
