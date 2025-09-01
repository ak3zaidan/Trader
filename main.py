import sys
import json
import time
import signal
from config import *
from app import TradeApp
from threading import Event
from datetime import datetime
from order import OrderManager
from thread import ticker_entry
from colorama import Fore, Style, init

init()

class TradingBot:
    def __init__(self):
        self.app = TradeApp()
        self.order_manager = OrderManager(self.app)
        self.monitors = {}  # ticker -> StockMonitor
        self.is_running = False
        self.stop_event = Event()
        
    def connect(self):
        """Connect to IBKR TWS"""
        try:
            success = self.app.connect_and_run(host, port, client_id)
            if success:
                print(f"{Fore.GREEN}Connected to IBKR TWS{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}Failed to connect to IBKR TWS{Style.RESET_ALL}")
                return False
            
        except Exception as e:
            print(f"{Fore.RED}Failed to connect to IBKR TWS: {e}{Style.RESET_ALL}")
            return False
    
    def load_tradable_tickers(self):
        """Load tradable tickers from tradable.json"""
        try:
            with open("tradable.json", "r") as f:
                tickers = json.load(f)
            print(f"{Fore.GREEN}Loaded {len(tickers)} tradable tickers{Style.RESET_ALL}")
            return tickers
        except FileNotFoundError:
            print(f"{Fore.RED}tradable.json not found. Please run filter_tickers.py first.{Style.RESET_ALL}")
            return []
        except Exception as e:
            print(f"{Fore.RED}Error loading tradable tickers: {e}{Style.RESET_ALL}")
            return []
    
    def wait_for_market_open(self):
        """Wait until market opens (6:30 AM PST)"""
        print(f"{Fore.YELLOW}Waiting for market open (6:30 AM PST)...{Style.RESET_ALL}")
        
        while True:
            now = datetime.now()
            market_open = now.replace(hour=6, minute=30, second=0, microsecond=0)
            
            if now >= market_open:
                print(f"{Fore.GREEN}Market is open! Starting trading bot...{Style.RESET_ALL}")
                break
            
            # Calculate time until market open
            time_until_open = market_open - now
            hours = int(time_until_open.total_seconds() // 3600)
            minutes = int((time_until_open.total_seconds() % 3600) // 60)
            
            print(f"{Fore.CYAN}Market opens in {hours}h {minutes}m{Style.RESET_ALL}")
            time.sleep(60)  # Check every minute
    
    def start_monitoring(self, tickers):
        """Start monitoring all tickers"""
        print(f"{Fore.GREEN}Starting monitoring for {len(tickers)} tickers...{Style.RESET_ALL}")
        
        # Start monitoring threads for each ticker
        for ticker in tickers:
            if not self.stop_event.is_set():
                try:
                    monitor = ticker_entry(ticker, self.app, self.order_manager)
                    self.monitors[ticker] = monitor
                    
                    # Small delay to avoid overwhelming the system
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"{Fore.RED}Error starting monitor for {ticker}: {e}{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}Started {len(self.monitors)} monitoring threads{Style.RESET_ALL}")
    
    def stop_all_monitors(self):
        """Stop all monitoring threads"""
        print(f"{Fore.YELLOW}Stopping all monitors...{Style.RESET_ALL}")
        
        for ticker, monitor in self.monitors.items():
            try:
                monitor.stop()
            except Exception as e:
                print(f"{Fore.RED}Error stopping monitor for {ticker}: {e}{Style.RESET_ALL}")
        
        self.monitors.clear()
        print(f"{Fore.GREEN}All monitors stopped{Style.RESET_ALL}")
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C signal"""
        print(f"\n{Fore.YELLOW}Received interrupt signal. Shutting down...{Style.RESET_ALL}")
        self.stop_event.set()
        self.stop_all_monitors()
        sys.exit(0)
    
    def run(self):
        """Main run loop"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Connect to IBKR
        if not self.connect():
            return
        
        # Load tradable tickers
        tickers = self.load_tradable_tickers()
        if not tickers:
            return
        
        # Wait for market open
        self.wait_for_market_open()
        
        # Start monitoring
        self.is_running = True
        self.start_monitoring(tickers)
        
        # Main loop - keep the bot running
        print(f"{Fore.GREEN}Trading bot is running. Press Ctrl+C to stop.{Style.RESET_ALL}")
        
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
                
                # Check if any monitors have stopped unexpectedly
                active_monitors = sum(1 for monitor in self.monitors.values() if monitor.is_running)
                if active_monitors < len(self.monitors):
                    print(f"{Fore.YELLOW}Warning: {len(self.monitors) - active_monitors} monitors have stopped{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_monitors()
            print(f"{Fore.GREEN}Trading bot stopped{Style.RESET_ALL}")

def main():
    """Main entry point"""
    print(f"{Fore.CYAN}=== Multi-Threaded Stock Trading Bot ==={Style.RESET_ALL}")
    print(f"{Fore.CYAN}Account Value: ${account_value:,}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Trade Size: {trade_size_percent}%{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Volume Price Ratio: {volume_price_ratio}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Max Volume Percent: {max_volume_percent}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Fast Mode Exit Minutes: {minutes_exit_fast_mode}{Style.RESET_ALL}")
    print()
    
    bot = TradingBot()
    bot.run()

if __name__ == '__main__':
    main()
