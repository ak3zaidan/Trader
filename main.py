from threading import Thread
from market_data import *
from config import *

def main(app):
    md1 = MarketData(app)

    for interval in [Interval.ONE_DAY_5MIN, Interval.ONE_WEEK_1HOUR, Interval.ONE_MONTH_1DAY]:
        bars = md1.get_historical_data("AAPL", interval)
        print(f"\nAAPL {interval.duration} {interval.bar_size} -> {len(bars)} bars")
        for bar in bars[:3]:
            print(bar.date, bar.close)

if __name__ == '__main__':
    app = TradeApp()
    app.connect(host, port, client_id)
    thread = Thread(target=app.run, daemon=True)
    thread.start()
    main(app=app)
