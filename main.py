from fastapi import FastAPI, Request
import requests, time, hmac, hashlib, json
import os

app = FastAPI()

# -----------------------------
# Bybit API kulcsok (Render környezeti változókból)
# -----------------------------
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE = "https://api.bybit.com"  # Mainnet

SYMBOL = "SOLUSDC"
QTY = 0.05

# -----------------------------
# HMAC aláírás a Bybithez
# -----------------------------
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

# -----------------------------
# Spot order küldése
# -----------------------------
def send_order(side):
    endpoint = "/v5/order/create"
    timestamp = str(int(time.time() * 1000))

    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "orderType": "Market",
        "qty": QTY
    }

    body_str = json.dumps(body)
    headers = bybit_headers(timestamp, body_str)

    r = requests.post(BASE + endpoint, json=body, headers=headers)

    # Logoljuk a raw response-ot, hogy lássuk minden visszajelzést
    print(f"Bybit raw response for {side}: {r.text}")

    try:
        return r.json()
    except json.JSONDecodeError:
        return {"error": "Nem sikerült feldolgozni a Bybit választ", "raw_response": r.text}

# -----------------------------
# FastAPI webhook
# -----------------------------
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    action = data.get("action", "").lower()

    if action == "buy":
        result = send_order("Buy")
        return {"status": "buy sent", "response": result}

    elif action == "sell":
        result = send_order("Sell")
        return {"status": "sell sent", "response": result}

    else:
        return {"error": "Ismeretlen action. Küldj 'buy' vagy 'sell'"}
