import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host = os.environ.get('DB_HOST'),
        database = os.environ.get('DB_NAME'),
        user = os.environ.get('DB_USER'),
        password = os.environ.get('DB_PASS')
    )

def insert_symbol(symbol, company_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO symbols (symbol, company_name) VALUES (%s, %s) ON CONFLICT (symbol) DO NOTHING", # %s are place holders for values and DO nothing means if the symbol exist skip it and do nothing 
        (symbol, company_name)
    )
    conn.commit()
    cursor.close()
    conn.close()

def insert_price(symbol_id, date, open_price, high, low, close, volume):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO stockprices (symbol_id, date, open, high, low, close, volume)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (symbol_id, date) DO NOTHING""",
        (symbol_id, date, open_price, high, low, close, volume)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_symbol_id(symbol):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM symbols WHERE symbol = %s", (symbol,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return result[0]
    return None