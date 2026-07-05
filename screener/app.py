from flask import Flask, render_template
from engine import top_gainers, top_losers, highest_volume, highest_Turnover, new_52_week_highs, new_52_week_lows
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    data = {
        'gainers': top_gainers().to_dict(orient='records'),
        'losers': top_losers().to_dict(orient='records'),
        'volume': highest_volume().to_dict(orient='records'),
        'turnover': highest_Turnover().to_dict(orient='records'),
        'new_highs': new_52_week_highs().to_dict(orient='records'),
        'new_lows': new_52_week_lows().to_dict(orient='records'),
        'date': datetime.datetime.now().strftime("%B %d, %Y")
    }
    return render_template('index.html', **data)

if __name__ == '__main__':
    app.run(debug=True)
