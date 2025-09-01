#!/usr/bin/env python3
"""
Test script for the trading bot components
"""

import json
from config import *
from app import TradeApp
from order import OrderManager
from market_data import MarketData

def test_connection():
    """Test IBKR connection"""
    print("Testing IBKR connection...")
    app = TradeApp()
    try:
        success = app.connect_and_run(host, port, client_id)
        if success:
            print("✅ Connection successful")
            return app
        else:
            print("❌ Connection failed")
            return None
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def test_market_data(app):
    """Test market data functionality"""
    print("\nTesting market data...")
    md = MarketData(app)
    
    # Test with a well-known stock
    test_ticker = "AAPL"
    tradable = md.is_tradable(test_ticker)
    print(f"✅ {test_ticker} tradable: {tradable}")
    
    # Test connection status
    status = app.get_connection_status()
    print(f"✅ Connection status: {status}")

def test_order_manager(app):
    """Test order manager functionality"""
    print("\nTesting order manager...")
    om = OrderManager(app)
    print("✅ Order manager initialized")
    
    # Test order ID generation
    try:
        order_id = app.get_next_order_id()
        print(f"✅ Next order ID: {order_id}")
    except Exception as e:
        print(f"⚠️  Order ID generation: {e}")

def test_tradable_loading():
    """Test loading tradable tickers"""
    print("\nTesting tradable tickers loading...")
    try:
        with open("tradable.json", "r") as f:
            tickers = json.load(f)
        print(f"✅ Loaded {len(tickers)} tradable tickers")
        if len(tickers) > 0:
            print(f"Sample tickers: {tickers[:5]}")
        return True
    except FileNotFoundError:
        print("❌ tradable.json not found. Run filter_tickers.py first.")
        return False
    except Exception as e:
        print(f"❌ Error loading tradable tickers: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Trading Bot Component Tests ===\n")
    
    # Test connection
    app = test_connection()
    if not app:
        return
    
    # Test market data
    test_market_data(app)
    
    # Test order manager
    test_order_manager(app)
    
    # Test tradable loading
    test_tradable_loading()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
