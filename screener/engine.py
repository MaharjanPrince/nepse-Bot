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
        WHERE p.date IN (
            SELECT DISTINCT date FROM stockprices 
            ORDER BY date DESC LIMIT 2
        )
        AND s.symbol != 'NEPSE'
        ORDER BY s.symbol, p.date
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

def get_stock_history(symbol, days = 365):
    engine = get_engine()
    query = f"""
        SELECT p.date, p.open, p.high, p.low, p.close, p.volume
        FROM stockprices p
        JOIN symbols s ON s.id = p.symbol_id
        WHERE s.symbol = '{symbol}'
        AND p.date >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY p.date ASC;
    """
    return pd.read_sql(query, engine)

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


import plotly.graph_objects as go

def get_stock_chart(symbol, days=365):
    df = get_stock_history(symbol, days)
    
    # Calculate indicators
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    df['rsi'] = calculate_rsi(df)
    
    # Create subplots — 2 rows, price on top, RSI below
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05
    )
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['date'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name=symbol
    ), row=1, col=1)
    
    # SMA lines
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['sma20'],
        name='SMA 20', line=dict(color='blue', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['sma50'],
        name='SMA 50', line=dict(color='orange', width=1)
    ), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['rsi'],
        name='RSI', line=dict(color='purple', width=1)
    ), row=2, col=1)
    
    # RSI reference lines
    fig.add_hline(y=70, line_dash='dash', line_color='red', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='green', row=2, col=1)
    
    fig.update_layout(
        title=f'{symbol} — Price History',
        xaxis_rangeslider_visible=False,
        height=650
    )
    
    return fig.to_html(full_html=False)

def get_stock_stats(symbol):
    df = get_stock_history(symbol, days=365)
    if df.empty:
        return None
    
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    df['rsi'] = calculate_rsi(df)
    
    latest = df.iloc[-1]
    
    current_rsi = round(latest['rsi'], 2)
    if current_rsi >= 70:
        rsi_signal = 'Overbought'
        rsi_color = 'red'
    elif current_rsi <= 30:
        rsi_signal = 'Oversold'
        rsi_color = 'green'
    else:
        rsi_signal = 'Neutral'
        rsi_color = 'gray'
    
    return {
        'symbol': symbol,
        'current_price': latest['close'],
        'week52_high': round(df['high'].max(), 2),
        'week52_low': round(df['low'].min(), 2),
        'avg_volume': int(df['volume'].mean()),
        'today_volume': int(latest['volume']),
        'sma20': round(latest['sma20'], 2),
        'sma50': round(latest['sma50'], 2),
        'above_sma20': latest['close'] > latest['sma20'],
        'above_sma50': latest['close'] > latest['sma50'],
        'rsi': current_rsi,
        'rsi_signal': rsi_signal,
        'rsi_color': rsi_color,
    }

# if __name__ == "__main__":
#     # df = get_latest_two_days()
#     # print(df)
#     # print(f"Rows: {len(df)}")

# #------_Debug--------------__#
#     # print("=== TOP GAINERS ===")
#     # print(top_gainers())

#     # print ("=== TOP LOSERS ===")
#     # print(top_losers())

#     # print ("=== HIGHEST VOLUME ===")
#     # print(highest_volume())

#     # print ("=== HIGHEST TURNOVER ===")
#     # print(highest_Turnover())

#     # print ("=== NEW 52 WEEK HIGHS ===")
#     # print(new_52_week_highs())

#     # print ("=== NEW 52 WEEK LOWS ===")
#     # print(new_52_week_lows())
#     df = get_stock_history("NABIL")
#     print(df.tail())
#     print(len(df))

#     html = get_stock_chart("NABIL")
#     print(html[:200])