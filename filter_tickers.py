from concurrent.futures import ThreadPoolExecutor, as_completed
from config import host, port, client_id
from market_data import MarketData
from threading import Thread
from app import TradeApp
import signal
import json
import sys
import os

THREADS = 1
results = []
existing_tradables = set()

def check_ticker(md: MarketData, ticker: str) -> dict:
    """Worker function to check tradability of a ticker."""
    tradable = md.is_tradable(ticker)
    return {"symbol": ticker, "tradable": tradable}

def save_results():
    """Save only tradable tickers as a string array in tradable.json."""
    all_tradables = existing_tradables.union({r["symbol"] for r in results if r["tradable"]})
    with open("tradable.json", "w") as f:
        json.dump(sorted(all_tradables), f, indent=2)
    print(f"\n✅ Saved {len(results)} new tradable tickers. Total tradables: {len(all_tradables)}")

def signal_handler(sig, frame):
    """Handle Ctrl+C signal and save progress."""
    print("\n⚠️  Ctrl+C detected! Saving results...")
    save_results()
    sys.exit(0)

def main(app):
    global results, existing_tradables
    md = MarketData(app)

    # Load all tickers
    with open("tickers.json", "r") as f:
        tickers = json.load(f)

    # Load already tradable tickers if file exists
    if os.path.exists("tradable.json"):
        with open("tradable.json", "r") as f:
            existing_data = json.load(f)
            existing_tradables = set(existing_data)

    # Filter tickers that still need checking
    tickers_to_check = [t for t in tickers if t not in existing_tradables]

    total = len(tickers_to_check)
    if total == 0:
        print("✅ All tickers already checked and saved as tradable.")
        return

    # Setup Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)

    # Use a thread pool for parallelism
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        future_to_ticker = {executor.submit(check_ticker, md, ticker): ticker for ticker in tickers_to_check}

        for i, future in enumerate(as_completed(future_to_ticker), start=1):
            result = future.result()
            results.append(result)
            ticker = result["symbol"]
            status = "✅ Tradable" if result["tradable"] else "❌ Not Tradable"
            print(f"[{i}/{total}] {ticker}: {status}")

    # Save all results after finishing
    save_results()
    print("✅ Finished checking tickers. Results saved to tradable.json")

if __name__ == "__main__":
    app = TradeApp()
    app.connect(host, port, client_id)
    thread = Thread(target=app.run, daemon=True)
    thread.start()
    main(app=app)
