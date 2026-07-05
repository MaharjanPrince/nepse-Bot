import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    return create_engine(db_url)

def get_latest_two_days():
    engine = get_engine()
    query = """
        SELECT s.symbol, p.date, p.close, p.volume
        FROM stockprices p
        JOIN symbols s ON s.id = p.symbol_id
        WHERE p.date >= (
            SELECT MAX(date) - INTERVAL '5 day'
            FROM stockprices
        )
        ORDER BY s.symbol, p.date;
        """
    return pd.read_sql(query, engine)

def get_price_changes():
    
    df = get_latest_two_days()
    
    dates = sorted(df['date'].unique())
    if len(dates) < 2:
        return None
    
    today = dates[-1]
    yesterday = dates[-2]
    
    today_df = df[df['date'] == today][['symbol', 'close']].rename(columns={'close': 'today_close'})
    yesterday_df = df[df['date'] == yesterday][['symbol', 'close']].rename(columns={'close': 'yesterday_close'})
    
    merged = pd.merge(today_df, yesterday_df, on='symbol')
    merged['change%'] = ((merged['today_close'] - merged['yesterday_close']) / merged['yesterday_close']) * 100
    merged['change%'] = merged['change%'].round(2)
    merged = merged[merged['change%'] != 0]  # ← after calculation
    
    return merged

def top_gainers(n=10):
    df = get_price_changes()
    return df.sort_values('change%', ascending=False).head(n)[['symbol', 'yesterday_close', 'today_close', 'change%']]

def top_losers(n=10):
    df = get_price_changes()
    return df.sort_values('change%', ascending=True).head(n)[['symbol', 'yesterday_close', 'today_close', 'change%']]

def highest_volume(n=10):
    df = get_latest_two_days()
    latest_date = df['date'].max()
    latest_df = df[df['date'] == latest_date]
    latest_df = latest_df[latest_df['symbol'] != 'NEPSE']
    return latest_df.sort_values('volume', ascending=False).head(n)[['symbol', 'close', 'volume']]

def highest_Turnover(n=10):
    df = get_latest_two_days()
    latest_date = df['date'].max()
    latest_df = df[df['date'] == latest_date]
    latest_df = latest_df[latest_df['symbol'] != 'NEPSE']
    latest_df['turnover'] = latest_df['close'] * latest_df['volume']
    return latest_df.sort_values('turnover', ascending=False).head(n)[['symbol', 'close', 'volume', 'turnover']]

def get_52_week_data():
    engine = get_engine()

    query = """
        SELECT
            s.symbol,
            p.date,
            p.high,
            p.low,
            p.close
        FROM stockprices p
        JOIN symbols s
            ON s.id = p.symbol_id
        WHERE p.date >= CURRENT_DATE - INTERVAL '365 days'
          AND s.symbol != 'NEPSE'
        ORDER BY s.symbol, p.date;
    """

    return pd.read_sql(query, engine)

def new_52_week_highs():
    df = get_52_week_data()
    
    today = df['date'].max()
    
    # Get yearly high EXCLUDING today
    historical = df[df['date'] < today]
    yearly_high = historical.groupby('symbol')['high'].max().reset_index()
    yearly_high.columns = ['symbol', 'yearly_high']
    
    today_df = df[df['date'] == today][['symbol', 'close']].rename(columns={'close': 'today_close'})
    
    merged = pd.merge(today_df, yearly_high, on='symbol')
    
    # today broke or matched the previous high
    highs = merged[merged['today_close'] >= merged['yearly_high']]
    
    return highs[['symbol', 'today_close', 'yearly_high']]


def new_52_week_lows():
    df = get_52_week_data()
    
    today = df['date'].max()
    
    # Get yearly low EXCLUDING today
    historical = df[df['date'] < today]
    yearly_low = historical.groupby('symbol')['low'].min().reset_index()
    yearly_low.columns = ['symbol', 'yearly_low']
    
    today_df = df[df['date'] == today][['symbol', 'close']].rename(columns={'close': 'today_close'})
    
    merged = pd.merge(today_df, yearly_low, on='symbol')
    
    # today broke or matched the previous low
    lows = merged[merged['today_close'] <= merged['yearly_low']]
    
    return lows[['symbol', 'today_close', 'yearly_low']]
if __name__ == "__main__":
    # df = get_latest_two_days()
    # print(df)
    # print(f"Rows: {len(df)}")


    print("=== TOP GAINERS ===")
    print(top_gainers())

    print ("=== TOP LOSERS ===")
    print(top_losers())

    print ("=== HIGHEST VOLUME ===")
    print(highest_volume())

    print ("=== HIGHEST TURNOVER ===")
    print(highest_Turnover())

    print ("=== NEW 52 WEEK HIGHS ===")
    print(new_52_week_highs())

    print ("=== NEW 52 WEEK LOWS ===")
    print(new_52_week_lows())
    