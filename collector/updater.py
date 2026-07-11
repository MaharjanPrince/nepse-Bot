import datetime
import time
import requests
import sys
import os
import pytz

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_connection, get_symbol_id, insert_price

nepal_tz = pytz.timezone('Asia/Kathmandu')

def get_latest_per_symbol():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.symbol, MAX(p.date) as latest_date
        FROM stockprices p
        JOIN symbols s ON s.id = p.symbol_id
        GROUP BY s.symbol;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {row[0]: row[1] for row in rows}

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://merolagani.com/",
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()

def main():
    run_start = datetime.datetime.now(nepal_tz)
    print("=" * 70)
    print(f"Run Started: {run_start}")
    print("=" * 70)

    end_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    latest_dates = get_latest_per_symbol()
    symbols = get_symbols_from_db()
    print(f"Checking {len(symbols)} symbols for updates...")

    processed = 0
    api_success = 0
    inserted_rows = 0
    failed = []

    for symbol in symbols:
        processed += 1
        try:
            latest = latest_dates.get(symbol)
            if latest:
                start_ts = int(datetime.datetime.combine(
                    latest - datetime.timedelta(days=1),
                    datetime.time.min
                ).replace(tzinfo=datetime.timezone.utc).timestamp())
            else:
                start_ts = int((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)).timestamp())

            data = fetch_recent_data(symbol, start_ts, end_ts)

            if data.get("s") != "ok" or "t" not in data:
                continue

            symbol_id = get_symbol_id(symbol)
            if symbol_id is None:
                continue

            api_success += 1
            for i in range(len(data["t"])):
                date = datetime.datetime.fromtimestamp(data["t"][i], datetime.timezone.utc).date()
                inserted = insert_price(
                    symbol_id,
                    date,
                    data["o"][i],
                    data["h"][i],
                    data["l"][i],
                    data["c"][i],
                    data["v"][i]
                )
                if inserted:
                    inserted_rows += 1

        except Exception as e:
            failed.append(symbol)
            print(f"[ERROR] {symbol:<10}: {e}")

        time.sleep(0.5)

    run_end = datetime.datetime.now(nepal_tz)
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Started  : {run_start}")
    print(f"Finished : {run_end}")
    print(f"Duration : {run_end - run_start}")
    print(f"Checked  : {processed}")
    print(f"Success  : {api_success}")
    print(f"Inserted : {inserted_rows}")
    print(f"Failed   : {len(failed)}")
    if failed:
        print("Failed symbols:", ", ".join(failed))
    print("=" * 70)

if __name__ == "__main__":
    main()