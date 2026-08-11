"""
NeuraTrade OS — 4H Trend Agent
Fetches BTCUSD 4-hour candle data from Delta Exchange India,
asks Gemini to identify the current trend direction,
saves the result into Supabase (market_data table).
"""

import os
import time
import json
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def fetch_4h_candles():
    end = int(time.time())
    start = end - (15 * 4 * 60 * 60)  # last 15 candles worth of time
    url = "https://api.india.delta.exchange/v2/history/candles"
    params = {
        "symbol": "BTCUSD",
        "resolution": "4h",
        "start": start,
        "end": end,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def ask_gemini(candles):
    prompt = (
        "You are a Market Analysis AI. Here is BTCUSD 4-hour candle data "
        "(OHLC) from Delta Exchange India, most recent candles included:\n\n"
        f"{json.dumps(candles)}\n\n"
        "Identify the current trend direction based on price structure "
        "(sequence of highs and lows). Respond in this exact short format:\n"
        "Trend: <Bullish/Bearish/Sideways>\n"
        "Reason: <one short sentence>\n"
        "Do not add any other text."
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def save_to_supabase(result_text):
    patch_url = f"{SUPABASE_URL}/rest/v1/market_data?symbol=eq.BTCUSD"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }
    body = {
        "trend_4h": result_text,
    }
    r = requests.patch(patch_url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    print("Saved to Supabase:", r.status_code)


def main():
    print("Fetching Delta Exchange 4H candles...")
    candles = fetch_4h_candles()

    print("Asking Gemini for trend analysis...")
    result = ask_gemini(candles)
    print("Gemini result:", result)

    print("Saving to Supabase...")
    save_to_supabase(result)

    print("4H Trend Agent run complete.")


if __name__ == "__main__":
    main()
