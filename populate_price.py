import requests
import datetime
import time
from db import get_connection, get_symbol_id, insert_price

def get_symbols_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM symbols")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def fetch_stock_data(symbol):
    url = f"https://merolagani.com/handlers/TechnicalChartHandler.ashx?type=get_advanced_chart&symbol={symbol}&resolution=1D&rangeStartDate=1746322045&rangeEndDate=1780450105&from=&isAdjust=1&currencyCode=NPR"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://merolagani.com/",
    }
    response = requests.get(url, headers=headers)
    return response.json()

def main():
    symbols = get_symbols_from_db()
    print(f"Total symbols to process: {len(symbols)}")

    for symbol in symbols:
        try:
            data = fetch_stock_data(symbol)

            if data.get('s') != 'ok' or 't' not in data:
                print(f"{symbol}: No data available")
                continue

            symbol_id = get_symbol_id(symbol)
            if symbol_id is None:
                print(f"{symbol}: Not found in symbols table")
                continue

            timestamps = data['t']
            opens = data['o']
            highs = data['h']
            lows = data['l']
            closes = data['c']
            volumes = data['v']

            for i in range(len(timestamps)):
                date = datetime.datetime.fromtimestamp(timestamps[i]).date()
                insert_price(
                    symbol_id,
                    date,
                    opens[i],
                    highs[i],
                    lows[i],
                    closes[i],
                    volumes[i]
                )

            print(f"{symbol}: Inserted {len(timestamps)} records")

        except Exception as e:
            print(f"{symbol}: Error - {e}")

        time.sleep(0.5) #very important this slows the request instead of hammering merolagani server 

if __name__ == "__main__":
    main()