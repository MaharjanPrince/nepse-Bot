import datetime
import time
import requests
import sys
import os
import pytz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection, get_symbol_id, insert_price

nepal_tz = pytz.timezone("Asia/Kathmandu")

def get_recent_timestamps():
    today = datetime.datetime.now(nepal_tz)
    three_days_ago = today - datetime.timedelta(days=3)

    return int(three_days_ago.timestamp()), int(today.timestamp())


def fetch_recent_data(symbol, start_timestamp, end_timestamp):
    url = (
        "https://merolagani.com/handlers/TechnicalChartHandler.ashx"
        f"?type=get_advanced_chart"
        f"&symbol={symbol}"
        f"&resolution=1D"
        f"&rangeStartDate={start_timestamp}"
        f"&rangeEndDate={end_timestamp}"
        f"&from="
        f"&isAdjust=1"
        f"&currencyCode=NPR"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://merolagani.com/",
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    return response.json()


def get_symbols_from_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT s.symbol 
        FROM symbols s
        INNER JOIN stockprices p ON p.symbol_id = s.id
        ORDER BY s.symbol;
    """)

    symbols = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return symbols


def main():

    run_start = datetime.datetime.now(nepal_tz)

    print("=" * 70)
    print(f"Run started : {run_start}")
    print("=" * 70)

    start_ts, end_ts = get_recent_timestamps()

    symbols = get_symbols_from_db()

    print(f"Checking {len(symbols)} symbols...")
    print()

    processed = 0
    api_success = 0
    inserted_rows = 0
    failed = []

    for symbol in symbols:
        processed += 1
        try:
            data = fetch_recent_data(symbol, start_ts, end_ts)
            if data.get("s") != "ok" or "t" not in data:
                continue

            symbol_id = get_symbol_id(symbol)
            if symbol_id is None:
                continue

            api_success += 1
            for i in range(len(data["t"])):
                date = datetime.datetime.fromtimestamp(data["t"][i], tz=nepal_tz).date()
                inserted = insert_price(
                    symbol_id, date,
                    data["o"][i], data["h"][i], data["l"][i],
                    data["c"][i], data["v"][i]
                )
                if inserted:
                    inserted_rows += 1

        except Exception as e:
            failed.append(symbol)
            print(f"[ERROR] {symbol:<10} {e}")

        time.sleep(0.30)   

    run_end = datetime.datetime.now(nepal_tz)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Started           : {run_start}")
    print(f"Finished          : {run_end}")
    print(f"Duration          : {run_end-run_start}")
    print(f"Symbols checked   : {processed}")
    print(f"API Success       : {api_success}")
    print(f"New rows inserted : {inserted_rows}")
    print(f"Failed symbols    : {len(failed)}")

    if failed:
        print()
        print("Failed:")
        print(", ".join(failed))

    print("=" * 70)


if __name__ == "__main__":
    main()