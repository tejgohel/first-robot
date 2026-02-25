from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

# ================= ENV VARIABLES =================
API_KEY = os.environ.get("DELTA_API_KEY")
API_SECRET = os.environ.get("DELTA_API_SECRET")
PRODUCT_ID = int(os.environ.get("PRODUCT_ID") or 1699)
ORDER_SIZE = int(os.environ.get("ORDER_SIZE") or 10)

# ================= DELTA CLIENT =================
delta_client = DeltaRestClient(
    base_url='https://cdn-ind.testnet.deltaex.org',
    api_key=API_KEY,
    api_secret=API_SECRET
)

current_position = None


def place_market_order(side):
    print(f"Placing MARKET {side} order...")
    response = delta_client.place_order(
        product_id=PRODUCT_ID,
        size=ORDER_SIZE,
        side=side.lower(),
        order_type=OrderType.MARKET,
    )
    print("Order Response:", response)
    return response


@app.route("/webhook", methods=["POST"])
def webhook():

    global current_position

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        signal_type = data.get("type")
        side = data.get("side")

        print("Received:", data)

        # ENTRY
        if signal_type == "ENTRY":
            if side == "BUY" and current_position != "BUY":
                place_market_order("buy")
                current_position = "BUY"

            elif side == "SELL" and current_position != "SELL":
                place_market_order("sell")
                current_position = "SELL"

        # EXIT
        elif signal_type == "EXIT":
            if side == "BUY_EXIT" and current_position == "BUY":
                place_market_order("sell")
                current_position = None

            elif side == "SELL_EXIT" and current_position == "SELL":
                place_market_order("buy")
                current_position = None

        return jsonify({"status": "Success"}), 200

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "🚀 Trading Bot Running 24x7 on Render"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)
