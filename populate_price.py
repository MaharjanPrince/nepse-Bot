import requests
import datetime
import time
from db import get_connection, get_symbol_id, insert_price

#Gets the symbols from the database that have at least one price record in the stockprices table. This ensures that we only fetch data for symbols that are already being tracked.
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

def fetch_stock_data(symbol):
    # Fetch from January 1, 2010 until now
    start = int(datetime.datetime(2010, 1, 1).timestamp())
    end = int(time.time())

    url = (
        "https://merolagani.com/handlers/TechnicalChartHandler.ashx"
        f"?type=get_advanced_chart"
        f"&symbol={symbol}"
        f"&resolution=1D"
        f"&rangeStartDate={start}"
        f"&rangeEndDate={end}"
        f"&from="
        f"&isAdjust=1"
        f"&currencyCode=NPR"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://merolagani.com/",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def main():
    symbols = get_symbols_from_db()
    print(f"Total symbols to process: {len(symbols)}")

    for symbol in symbols:
        try:
            data = fetch_stock_data(symbol)

            if data.get("s") != "ok" or "t" not in data:
                print(f"{symbol}: No data available")
                continue

            symbol_id = get_symbol_id(symbol)
            if symbol_id is None:
                print(f"{symbol}: Not found in symbols table")
                continue

            timestamps = data["t"]
            opens = data["o"]
            highs = data["h"]
            lows = data["l"]
            closes = data["c"]
            volumes = data["v"]

            inserted = 0

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
                inserted += 1

            if inserted:
                first_date = datetime.datetime.fromtimestamp(timestamps[0]).date()
                last_date = datetime.datetime.fromtimestamp(timestamps[-1]).date()
                print(f"{symbol}: Inserted {inserted} records ({first_date} → {last_date})")
            else:
                print(f"{symbol}: No records inserted")

        except Exception as e:
            print(f"{symbol}: Error - {e}")

        # Don't hammer the server
        time.sleep(0.3)

if __name__ == "__main__":
    main()