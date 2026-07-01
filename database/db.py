import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection and operations
def get_connection():
    return psycopg2.connect(
        host = os.environ.get('DB_HOST'),
        database = os.environ.get('DB_NAME'),
        user = os.environ.get('DB_USER'),
        password = os.environ.get('DB_PASS')
    )

#Function to insert a new symbol into the symbols table with its company name. If the symbol already exists, it does nothing.
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

#Function to insert a new price record into the stockprices table. If a record for the same symbol and date already exists, it does nothing.
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

#Function to get the ID of a symbol from the symbols table. Returns None if the symbol does not exist.
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