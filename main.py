from fastapi import FastAPI, Request
import requests, time, hmac, hashlib, json, os
import uvicorn

app = FastAPI()

# -----------------------------
# Bybit API kulcsok (Render Environment Variables-ben állítsd be)
# -----------------------------
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE = "https://api.bybit.com"  # Mainnet

SYMBOL = "SOLUSDC"
QTY = 0.1  # Fél SOL 0.1-hez, kicsi teszt pozíció

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

    try:
        r = requests.post(BASE + endpoint, json=body, headers=headers, timeout=10)
        print(f"[{time.strftime('%X')}] Bybit raw response for {side}: {r.text}")
        return r.json()
    except Exception as e:
        print(f"[{time.strftime('%X')}] Bybit request error: {e}")
        return {"error": str(e)}

# -----------------------------
# FastAPI webhook
# -----------------------------
@app.post("/webhook")
async def webhook(request: Request):
    try:
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

    except Exception as e:
        return {"error": "Webhook feldolgozási hiba", "details": str(e)}

# -----------------------------
# Render-ready Uvicorn indítás
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
