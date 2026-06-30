import requests 
from db import insert_symbol

def get_all_symbol():
    url = "https://merolagani.com/handlers/AutoSuggestHandler.ashx?type=Company"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://merolagani.com/",
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def main():
    symbols_data = get_all_symbol()
    print(f"Found {len(symbols_data)} symbols")

    for item in symbols_data:
        symbol = item['d']
        company_name = item['l']
        insert_symbol(symbol, company_name)
        print(f"Inserted: {symbol}")
        
if __name__ == "__main__":
    main()