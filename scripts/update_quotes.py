#!/usr/bin/env python
import pprint
import requests
import yfinance as yf
from datetime import datetime


def main():
    tickers = ["VTI", "GLD", "PSTG", "ORCL", "STRC", "BTC-USD"]
    ticker_objs = {t: yf.Ticker(t) for t in tickers}

    quotes = {}

    for t in tickers:
        try:
            data = ticker_objs[t].history(period="1d", interval="1m")
            quotes[t] = f"{data['Close'].iloc[-1]:.2f}" if not data.empty else "N/A"
        except:
            quotes[t] = "N/A"

    quotes["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pprint.pprint(quotes)
    url = "http://127.0.0.1:8000/api/minion-quotes"
    response = requests.post(url, json=quotes)
    pprint.pprint(response.status_code)
    pprint.pprint(response.json())


if __name__ == "__main__":
    main()
