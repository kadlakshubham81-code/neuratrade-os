"""
NeuraTrade OS — 15M BOS/FVG Agent
Fetches BTCUSD 15-minute candle data from Delta Exchange India,
asks Gemini to detect Break of Structure (BOS) and Fair Value Gap (FVG),
saves the result into Supabase (market_data table).
"""

import os
import time
import json
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def fetch_15m_candles():
    end = int(time.time())
    start = end - (25 * 15 * 60)  # last ~25 candles worth of time
    url = "https://api.india.delta.exchange/v2/history/candles"
    params = {
        "symbol": "BTCUSD",
        "resolution": "15m",
        "start": start,
        "end": end,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def ask_gemini(candles):
    prompt = (
        "You are a Market Analysis AI specializing in Smart Money Concepts. "
        "Here is BTCUSD 15-minute candle data (OHLC) from Delta Exchange India:\n\n"
        f"{json.dumps(candles)}\n\n"
        "Identify if a Break of Structure (BOS) has occurred and if any Fair "
        "Value Gap (FVG) has formed recently. Respond in this exact short format:\n"
        "Significant: <Yes/No>\n"
        "BOS: <Yes/No>\n"
        "FVG: <Yes/No, with price range if Yes>\n"
        "Details: <one short sentence, or 'None' if nothing significant>\n"
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
        "bos_fvg_15m": result_text,
    }
    r = requests.patch(patch_url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    print("Saved to Supabase:", r.status_code)


def main():
    print("Fetching Delta Exchange 15M candles...")
    candles = fetch_15m_candles()

    print("Asking Gemini for BOS/FVG analysis...")
    result = ask_gemini(candles)
    print("Gemini result:", result)

    print("Saving to Supabase...")
    save_to_supabase(result)

    print("15M BOS/FVG Agent run complete.")


if __name__ == "__main__":
    main()
