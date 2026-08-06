"""
NeuraTrade OS — Daily Agent
Fetches BTCUSD daily candle data from Delta Exchange India,
asks Gemini to identify previous day's high/low,
saves the result into Supabase (market_data table).
"""

import os
import time
import json
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def fetch_daily_candles():
    end = int(time.time())
    start = end - (4 * 24 * 60 * 60)  # last 4 days
    url = "https://api.india.delta.exchange/v2/history/candles"
    params = {
        "symbol": "BTCUSD",
        "resolution": "1d",
        "start": start,
        "end": end,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def ask_gemini(candles):
    prompt = (
        "You are a Market Analysis AI. Here is BTCUSD daily candle data "
        "(OHLC) from Delta Exchange India:\n\n"
        f"{json.dumps(candles)}\n\n"
        "Identify the previous completed day's High and Low. "
        "Respond in this exact short format:\n"
        "Date: <date>\nHigh: <value>\nLow: <value>\n"
        "Do not add any other text."
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def save_to_supabase(result_text):
    url = f"{SUPABASE_URL}/rest/v1/market_data"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }
    # Update the single BTCUSD row (id=1 assumed first row)
    patch_url = f"{SUPABASE_URL}/rest/v1/market_data?symbol=eq.BTCUSD"
    body = {
        "daily_high_low": result_text,
        "updated_at": "now()",
    }
    r = requests.patch(patch_url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    print("Saved to Supabase:", r.status_code)


def main():
    print("Fetching Delta Exchange daily candles...")
    candles = fetch_daily_candles()

    print("Asking Gemini for analysis...")
    result = ask_gemini(candles)
    print("Gemini result:", result)

    print("Saving to Supabase...")
    save_to_supabase(result)

    print("Daily Agent run complete.")


if __name__ == "__main__":
    main()
