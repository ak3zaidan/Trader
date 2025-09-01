import csv
import time
import threading
from config import *
from app import TradeApp
from datetime import datetime
from order import OrderManager
from polygon import RESTClient
from typing import Dict, Optional
from colorama import Fore, Style, init

init()

class StockMonitor:
    def __init__(self, ticker: str, app: TradeApp, order_manager: OrderManager):
        self.ticker = ticker
        self.app = app
        self.order_manager = order_manager
        self.polygon_client = RESTClient(polygon_api_key)
        
        # State management
        self.is_running = False
        self.current_price = 0.0
        self.price_history = []  # [(timestamp, price), ...]
        self.trigger_price = 0.0
        self.entry_price = 0.0
        self.shares_bought = 0
        self.order_id = None
        self.stop_loss_order_id = None
        
        # Trading states
        self.state = "monitoring"  # monitoring, fast_mode, buy_stage, active_trade
        self.fast_mode_start_time = None
        self.buy_stage_start_time = None
        self.trade_start_time = None
        self.last_cooldown_time = None
        
        # Volume tracking
        self.today_volume = 0
        self.avg_volume = 0
        
        # Thread control
        self.thread = None
        self.should_stop = False
        
    def start(self):
        """Start the monitoring thread"""
        if self.thread is None or not self.thread.is_alive():
            self.is_running = True
            self.should_stop = False
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            self._log(f"{Fore.GREEN}Started monitoring{Style.RESET_ALL}")
    
    def stop(self):
        """Stop the monitoring thread"""
        self.should_stop = True
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self._log(f"{Fore.RED}Stopped monitoring{Style.RESET_ALL}")
    
    def _log(self, message: str):
        """Log message with timestamp and ticker"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.ticker}: {message}")
    
    def _get_current_price(self) -> Optional[float]:
        """Get current price from Polygon API"""
        try:
            # Get latest trade
            trades = self.polygon_client.get_last_trade(self.ticker)
            if trades and hasattr(trades, 'results') and trades.results:
                return float(trades.results[0].p)  # price
            return None
        except Exception as e:
            self._log(f"{Fore.RED}Error getting price: {e}{Style.RESET_ALL}")
            return None
    
    def _get_volume_data(self) -> Dict:
        """Get volume data for the day"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            # Get daily aggregates
            aggregates = self.polygon_client.get_aggs(
                self.ticker, 1, "day", today, today
            )
            
            if aggregates and len(aggregates) > 0:
                agg = aggregates[0]
                return {
                    "today_volume": agg.v,  # volume
                    "avg_volume": agg.v  # For now, use today's volume as avg
                }
            return {"today_volume": 0, "avg_volume": 0}
        except Exception as e:
            self._log(f"{Fore.RED}Error getting volume: {e}{Style.RESET_ALL}")
            return {"today_volume": 0, "avg_volume": 0}
    
    def _check_filter_conditions(self) -> bool:
        """Check if stock should be filtered out"""
        if self.current_price < 0.1:
            self._log(f"{Fore.YELLOW}Price below $0.1, filtering out{Style.RESET_ALL}")
            return False
        
        if self.avg_volume < 1000000:  # 1M volume
            self._log(f"{Fore.YELLOW}Average volume below 1M, filtering out{Style.RESET_ALL}")
            return False
        
        return True
    
    def _check_trigger_condition(self) -> bool:
        """Check if 15% consecutive gain trigger is met"""
        if len(self.price_history) < 2:
            return False
        
        current_price = self.price_history[-1][1]
        
        # Check for 15% gain from any point in history
        for timestamp, price in self.price_history[:-1]:
            gain_percent = ((current_price - price) / price) * 100
            if gain_percent >= 15:
                self.trigger_price = price
                self._log(f"{Fore.CYAN}Trigger condition met: {gain_percent:.2f}% gain from ${price:.2f}{Style.RESET_ALL}")
                return True
        
        return False
    
    def _check_volume_conditions(self) -> bool:
        """Check volume conditions for trading"""
        if self.current_price <= 0:
            return False
        
        # Condition 1: Today's volume > (current_price × volume_price_ratio)
        volume_condition_1 = self.today_volume > (self.current_price * volume_price_ratio)
        
        # Condition 2: max_volume_percent > (account_value × trade_size_percent) / ((today_volume × current_price) / hours_since_market_open)
        hours_since_open = max(1, (datetime.now().hour - 6.5))  # Market opens at 6:30 AM PST
        trade_amount = (account_value * trade_size_percent) / 100
        volume_denominator = (self.today_volume * self.current_price) / hours_since_open
        volume_condition_2 = max_volume_percent > (trade_amount / volume_denominator) if volume_denominator > 0 else False
        
        if volume_condition_1 and volume_condition_2:
            self._log(f"{Fore.GREEN}Volume conditions met{Style.RESET_ALL}")
            return True
        
        return False
    
    def _enter_fast_mode(self):
        """Enter fast mode after trigger conditions are met"""
        self.state = "fast_mode"
        self.fast_mode_start_time = datetime.now()
        self._log(f"{Fore.MAGENTA}Entering fast mode{Style.RESET_ALL}")
    
    def _check_fast_mode_exit_conditions(self) -> bool:
        """Check if should exit fast mode"""
        if not self.fast_mode_start_time:
            return False
        
        current_price = self.price_history[-1][1]
        initial_trigger_price = self.trigger_price
        
        # Exit if 80% of original gain lost
        original_gain = ((current_price - initial_trigger_price) / initial_trigger_price) * 100
        if original_gain < 3:  # 15% * 0.2 = 3%
            self._log(f"{Fore.YELLOW}Exiting fast mode: 80% of gain lost{Style.RESET_ALL}")
            return True
        
        # Exit if exceeded time limit
        time_in_fast_mode = (datetime.now() - self.fast_mode_start_time).total_seconds() / 60
        if time_in_fast_mode > minutes_exit_fast_mode:
            self._log(f"{Fore.YELLOW}Exiting fast mode: time limit exceeded{Style.RESET_ALL}")
            return True
        
        # Check for negative slope (simplified)
        if len(self.price_history) >= 3:
            recent_prices = [p[1] for p in self.price_history[-3:]]
            if recent_prices[-1] < recent_prices[-2] < recent_prices[-3]:
                self._log(f"{Fore.YELLOW}Exiting fast mode: negative slope detected{Style.RESET_ALL}")
                return True
        
        return False
    
    def _check_buy_conditions(self) -> bool:
        """Check if ready to enter buy stage"""
        if not self.fast_mode_start_time:
            return False
        
        current_price = self.price_history[-1][1]
        
        # Current price 5% above initial trigger price
        price_condition = current_price >= self.trigger_price * 1.05
        
        # Gradual gain over 5+ minutes (no sudden jumps)
        time_in_fast_mode = (datetime.now() - self.fast_mode_start_time).total_seconds() / 60
        time_condition = time_in_fast_mode >= 5
        
        # Positive 1-minute slope for past 2 minutes
        slope_condition = False
        if len(self.price_history) >= 4:  # Need at least 4 data points for 2-minute slope
            recent_prices = [p[1] for p in self.price_history[-4:]]
            if recent_prices[-1] > recent_prices[-2] > recent_prices[-3]:
                slope_condition = True
        
        if price_condition and time_condition and slope_condition:
            self._log(f"{Fore.GREEN}Buy conditions met!{Style.RESET_ALL}")
            return True
        
        return False
    
    def _enter_buy_stage(self):
        """Enter buy stage"""
        self.state = "buy_stage"
        self.buy_stage_start_time = datetime.now()
        self._log(f"{Fore.BLUE}Entering buy stage{Style.RESET_ALL}")
        
        # Place limit order
        current_price = self.price_history[-1][1]
        trade_amount = (account_value * trade_size_percent) / 100
        shares_to_buy = int(trade_amount / current_price)
        
        if shares_to_buy > 0:
            self.order_id = self.order_manager.place_limit_order(
                self.ticker, shares_to_buy, current_price
            )
            self._log(f"{Fore.BLUE}Placed limit order: {shares_to_buy} shares at ${current_price:.2f}{Style.RESET_ALL}")
    
    def _check_buy_fill(self) -> bool:
        """Check if buy order was filled"""
        if not self.order_id:
            return False
        
        # Check order status
        open_orders = self.order_manager.get_open_orders()
        if self.order_id not in open_orders:
            # Order was filled or cancelled
            executions = self.order_manager.get_executions()
            for exec_id, execution in executions.items():
                if execution.get('symbol') == self.ticker:
                    self.shares_bought = execution['shares']
                    self.entry_price = execution['price']
                    self._log(f"{Fore.GREEN}Order filled: {self.shares_bought} shares at ${self.entry_price:.2f}{Style.RESET_ALL}")
                    return True
        
        # Check if order timed out (1 minute)
        if self.buy_stage_start_time:
            time_in_buy_stage = (datetime.now() - self.buy_stage_start_time).total_seconds()
            if time_in_buy_stage > 60:  # 1 minute timeout
                self.order_manager.cancel_order(self.order_id)
                self._log(f"{Fore.YELLOW}Buy order timed out, cancelling{Style.RESET_ALL}")
                self.state = "fast_mode"
                self.order_id = None
        
        return False
    
    def _enter_active_trade(self):
        """Enter active trade management"""
        self.state = "active_trade"
        self.trade_start_time = datetime.now()
        self._log(f"{Fore.GREEN}Entering active trade management{Style.RESET_ALL}")
        
        # Set 2% trailing stop loss
        stop_price = self.entry_price * 0.98
        self.stop_loss_order_id = self.order_manager.place_trailing_stop(
            self.ticker, self.shares_bought, self.entry_price * 0.02  # 2% trail
        )
        self._log(f"{Fore.GREEN}Set trailing stop loss at ${stop_price:.2f}{Style.RESET_ALL}")
    
    def _check_exit_conditions(self) -> bool:
        """Check if should exit active trade"""
        if not self.trade_start_time:
            return False
        
        current_price = self.price_history[-1][1]
        profit_percent = ((current_price - self.entry_price) / self.entry_price) * 100
        
        # 3% profit: sell immediately
        if profit_percent >= 3:
            self._log(f"{Fore.GREEN}Exit condition: 3% profit reached{Style.RESET_ALL}")
            return True
        
        # 1%+ profit + slope turns flat/negative
        if profit_percent >= 1:
            if len(self.price_history) >= 3:
                recent_prices = [p[1] for p in self.price_history[-3:]]
                if recent_prices[-1] <= recent_prices[-2]:
                    self._log(f"{Fore.YELLOW}Exit condition: 1%+ profit with flat/negative slope{Style.RESET_ALL}")
                    return True
        
        # 10+ minutes elapsed
        time_in_trade = (datetime.now() - self.trade_start_time).total_seconds() / 60
        if time_in_trade >= 10:
            self._log(f"{Fore.YELLOW}Exit condition: 10+ minutes elapsed{Style.RESET_ALL}")
            return True
        
        return False
    
    def _exit_trade(self, reason: str):
        """Exit the active trade"""
        # Place market sell order
        sell_order_id = self.order_manager.place_market_order(
            self.ticker, self.shares_bought, "SELL"
        )
        
        # Calculate final profit
        current_price = self.price_history[-1][1]
        final_profit = ((current_price - self.entry_price) / self.entry_price) * 100
        
        # Log trade result
        self._log(f"{Fore.CYAN}Exiting trade: {reason}, Profit: {final_profit:.2f}%{Style.RESET_ALL}")
        
        # Save trade record
        self._save_trade_record(reason, final_profit)
        
        # Reset state
        self.state = "monitoring"
        self.shares_bought = 0
        self.entry_price = 0.0
        self.order_id = None
        self.stop_loss_order_id = None
        self.trade_start_time = None
        self.last_cooldown_time = datetime.now()
    
    def _save_trade_record(self, exit_reason: str, profit_percent: float):
        """Save trade record to CSV"""
        try:
            filename = "trades.csv"
            file_exists = False
            
            try:
                with open(filename, 'r') as f:
                    file_exists = True
            except FileNotFoundError:
                pass
            
            with open(filename, 'a', newline='') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    # Write header
                    writer.writerow([
                        'timestamp', 'ticker', 'entry_price', 'exit_price', 'shares',
                        'profit_percent', 'duration_minutes', 'exit_reason', 'win_loss'
                    ])
                
                # Calculate duration
                duration = 0
                if self.trade_start_time:
                    duration = (datetime.now() - self.trade_start_time).total_seconds() / 60
                
                current_price = self.price_history[-1][1]
                win_loss = "WIN" if profit_percent > 0 else "LOSS"
                
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    self.ticker,
                    f"{self.entry_price:.2f}",
                    f"{current_price:.2f}",
                    self.shares_bought,
                    f"{profit_percent:.2f}",
                    f"{duration:.1f}",
                    exit_reason,
                    win_loss
                ])
                
        except Exception as e:
            self._log(f"{Fore.RED}Error saving trade record: {e}{Style.RESET_ALL}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running and not self.should_stop:
            try:
                # Get current price
                price = self._get_current_price()
                if price is None:
                    time.sleep(30)
                    continue
                
                self.current_price = price
                self.price_history.append((datetime.now(), price))
                
                # Keep only last 100 price points
                if len(self.price_history) > 100:
                    self.price_history = self.price_history[-100:]
                
                # Get volume data every 5 minutes
                if len(self.price_history) % 10 == 0:  # Every 5 minutes (10 * 30 seconds)
                    volume_data = self._get_volume_data()
                    self.today_volume = volume_data["today_volume"]
                    self.avg_volume = volume_data["avg_volume"]
                
                # Check filter conditions
                if not self._check_filter_conditions():
                    self.stop()
                    break
                
                # State machine
                if self.state == "monitoring":
                    if self._check_trigger_condition() and self._check_volume_conditions():
                        self._enter_fast_mode()
                
                elif self.state == "fast_mode":
                    if self._check_fast_mode_exit_conditions():
                        self.state = "monitoring"
                    elif self._check_buy_conditions():
                        self._enter_buy_stage()
                
                elif self.state == "buy_stage":
                    if self._check_buy_fill():
                        self._enter_active_trade()
                
                elif self.state == "active_trade":
                    if self._check_exit_conditions():
                        self._exit_trade("exit_condition_met")
                
                # Check cooldown
                if self.last_cooldown_time:
                    cooldown_elapsed = (datetime.now() - self.last_cooldown_time).total_seconds() / 60
                    if cooldown_elapsed < 5:  # 5-minute cooldown
                        time.sleep(30)
                        continue
                
                # Sleep based on state
                if self.state == "monitoring":
                    time.sleep(30)  # 30-second intervals
                elif self.state == "fast_mode":
                    time.sleep(15)  # 15-second intervals
                elif self.state == "buy_stage":
                    time.sleep(5)   # 5-second intervals
                elif self.state == "active_trade":
                    time.sleep(1)   # 1-second intervals
                
            except Exception as e:
                self._log(f"{Fore.RED}Error in monitor loop: {e}{Style.RESET_ALL}")
                time.sleep(30)

def ticker_entry(ticker: str, app: TradeApp, order_manager: OrderManager):
    """Entry point for each ticker thread"""
    monitor = StockMonitor(ticker, app, order_manager)
    monitor.start()
    return monitor
