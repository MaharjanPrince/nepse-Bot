import datetime
import time
import requests
from db import get_connection, get_symbol_id, insert_price

def get_recent_timestamps():
    today = datetime.datetime.now()
    three_days_ago = today - datetime.timedelta(days=3)
    
    end_timestamp = int(today.timestamp())
    start_timestamp = int(three_days_ago.timestamp())
    
    return start_timestamp, end_timestamp


def fetch_recent_data(symbol, start_timestamp, end_timestamp):
    url = f"https://merolagani.com/handlers/TechnicalChartHandler.ashx?type=get_advanced_chart&symbol={symbol}&resolution=1D&rangeStartDate={start_timestamp}&rangeEndDate={end_timestamp}&from=&isAdjust=1&currencyCode=NPR"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://merolagani.com/",
    }
    response = requests.get(url, headers=headers)
    return response.json()


def get_symbols_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT s.symbol 
        FROM symbols s
        INNER JOIN stockprices p ON p.symbol_id = s.id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def main():
    start, end = get_recent_timestamps()
    symbols = get_symbols_from_db()
    print(f"Updating {len(symbols)} symbols...")

    updated_count = 0
    for symbol in symbols:
        try:
            data = fetch_recent_data(symbol, start, end)

            if data.get('s') != 'ok' or 't' not in data:
                continue

            symbol_id = get_symbol_id(symbol)
            if symbol_id is None:
                continue

            for i in range(len(data['t'])):
                date = datetime.datetime.fromtimestamp(data['t'][i]).date()
                insert_price(
                    symbol_id,
                    date,
                    data['o'][i],
                    data['h'][i],
                    data['l'][i],
                    data['c'][i],
                    data['v'][i]
                )
            updated_count += 1

        except Exception as e:
            print(f"{symbol}: Error - {e}")

        time.sleep(0.3)

    print(f"Done. Updated {updated_count} symbols.")

if __name__ == "__main__":
    main()