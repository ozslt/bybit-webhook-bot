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
    timestamp = str(int(time.time()*1000))

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

    r = requests.post(BASE + endpoint, json=body, headers=headers)
    return r.json()


def get_entry_price(symbol):
    endpoint = "/v5/position/list"
    timestamp = str(int(time.time()*1000))

    params = {
        "category": "linear",
        "symbol": symbol
    }

    query = json.dumps(params)
    headers = bybit_headers(timestamp, query)
    r = requests.get(BASE + endpoint, params=params, headers=headers)
    data = r.json()

    try:
        return float(data["result"]["list"][0]["avgPrice"])
    except:
        return None


def set_stop_loss(symbol, sl_price):
    endpoint = "/v5/position/trading-stop"
    timestamp = str(int(time.time()*1000))

    body = {
        "category": "linear",
        "symbol": symbol,
        "stopLoss": str(sl_price)
    }

    body_str = json.dumps(body)
    headers = bybit_headers(timestamp, body_str)

    return requests.post(BASE + endpoint, json=body, headers=headers).json()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    action = data.get("action")
    symbol = data.get("symbol")
    qty = data.get("qty")

    if not action or not symbol or not qty:
        return {"error": "Missing fields"}

    if action.lower() == "buy":
        send_order(symbol, "Sell", qty)
        order = send_order(symbol, "Buy", qty)
        time.sleep(0.5)

        entry = get_entry_price(symbol)
        if entry:
            sl = round(entry * 0.97, 4)
            sl_res = set_stop_loss(symbol, sl)
            return {"order": order, "stop_loss": sl_res}

        return {"order": order, "warning": "No entry price found"}

    elif action.lower() == "sell":
        send_order(symbol, "Buy", qty)
        order = send_order(symbol, "Sell", qty)
        time.sleep(0.5)

        entry = get_entry_price(symbol)
        if entry:
            sl = round(entry * 1.03, 4)
            sl_res = set_stop_loss(symbol, sl)
            return {"order": order, "stop_loss": sl_res}

        return {"order": order, "warning": "No entry price found"}

    return {"error": "Unknown action"}
