# Multi-Threaded Stock Trading Bot

## Overview
A Python trading bot that monitors ~12,000 stocks simultaneously using threading, executing momentum-based trades with strict risk management. The bot connects to IBKR Trader Workstation and places actual trades through the IBKR TWS API. Due to API limitations, it uses polling via Polygon REST API for market data (unlimited API calls).

## Features
- **Multi-threaded monitoring** of thousands of stocks simultaneously
- **Momentum-based trading strategy** with 15% gain triggers
- **Risk management** with trailing stops and position limits
- **Real-time market data** via Polygon API
- **Actual trade execution** via IBKR TWS
- **Comprehensive logging** with colored console output
- **Trade record tracking** in CSV format
- **Automatic filtering** of low-price and low-volume stocks

## Architecture
- **main.py**: Launch controller that creates threads for each ticker from `tradable.json`
- **thread.py**: Contains the StockMonitor class (one instance per ticker)
- **app.py**: IBKR TWS connection and API wrapper
- **order.py**: Order management and execution
- **market_data.py**: Market data fetching and validation
- **config.py**: Configuration variables and API keys

## Installation

### 1. Install Dependencies
```bash
pip install -r requirments.txt
```

### 2. Setup IBKR Trader Workstation
1. Download and install [IBKR Trader Workstation](https://www.interactivebrokers.com/en/trading/tws.php)
2. Enable API connections in TWS:
   - File → Global Configuration → API → Settings
   - Enable "Enable ActiveX and Socket Clients"
   - Set port to 7497 (paper trading) or 7496 (live trading)
   - Add your IP to "Trusted IPs" or disable "Read-Only API"

### 3. Configure API Keys
Edit `config.py` with your API keys:
```python
# IBKR config
paper_trading = True  # Set to False for live trading
host = "127.0.0.1"
port = 7497  # 7497 for paper, 7496 for live
client_id = 0

# Polygon config
polygon_api_key = "YOUR_POLYGON_API_KEY"
```

### 4. Collect Tradable Tickers
```bash
# Step 1: Collect all tickers from Polygon
python collect.py

# Step 2: Filter for tradable tickers on IBKR
python filter_tickers.py
```

## Configuration

### Trading Parameters (config.py)
- `account_value`: Total account value for position sizing
- `trade_size_percent`: Percentage of account to risk per trade (100% = full account)
- `volume_price_ratio`: Volume must be this many times larger than current price
- `max_volume_percent`: Maximum percentage of daily volume to trade
- `minutes_exit_fast_mode`: Time limit for fast mode before reverting to monitoring

### Risk Management
- **Single trade limit**: Only 1 active position at a time
- **Cooldown period**: 5-minute wait before re-trading same stock
- **Trailing stop loss**: 2% trailing stop on all positions
- **Position filtering**: Stocks below $0.10 or 1M average volume are filtered out

## Trading Strategy

### 1. Monitoring Phase (30-second intervals)
- Fetch current price every 30 seconds
- Store price + timestamp in array
- **Trigger condition**: Find ≥15% consecutive gain from any point in array to current price
- **Volume checks** (both must pass):
  - Today's volume > (current_price × volume_price_ratio)
  - max_volume_percent > (account_value × trade_size_percent) / ((today_volume × current_price) / hours_since_market_open)

### 2. Fast Mode (15-second intervals)
**Entry**: After passing monitoring phase checks
**Exit conditions** (return to monitoring):
- 80% of original gain lost
- Overall negative slope detected  
- Exceeded minutes_exit_fast_mode duration

**Advance to buy stage** when ALL met:
- Current price 5% above initial trigger price
- Gradual gain over 5+ minutes (no sudden jumps)
- Positive 1-minute slope for past 2 minutes
- No other active trades

### 3. Buy Stage
- Place limit order: current_price × (account_value × trade_size_percent)
- Wait 1 minute for fill
- If no fill: cancel order, return to fast mode
- If filled: proceed to active phase

### 4. Active Trade Management
- **Immediate**: Set 2% trailing stop loss
- **Real-time monitoring**: Polygon REST API polling every 1s
- **Exit conditions**:
  - 3% profit: sell immediately
  - 1%+ profit + slope turns flat/negative: sell
  - 10+ minutes elapsed: sell

## Usage

### Start the Trading Bot
```bash
python main.py
```

The bot will:
1. Connect to IBKR TWS
2. Load tradable tickers from `tradable.json`
3. Wait for market open (6:30 AM PST)
4. Start monitoring all tickers simultaneously
5. Execute trades based on the strategy

### Stop the Bot
Press `Ctrl+C` to gracefully shut down all monitoring threads.

## Output Files

### trades.csv
Complete trade records with columns:
- timestamp: Trade execution time
- ticker: Stock symbol
- entry_price: Purchase price
- exit_price: Sale price
- shares: Number of shares traded
- profit_percent: Profit/loss percentage
- duration_minutes: Time in trade
- exit_reason: Reason for exit
- win_loss: WIN or LOSS

### Console Output
- **Green**: Successful operations, profits
- **Red**: Errors, losses
- **Yellow**: Warnings, exits
- **Cyan**: Information, triggers
- **Magenta**: State changes
- **Blue**: Order placement

## Testing

### Test Components
```bash
python test.py
```

This will test:
- IBKR connection
- Market data functionality
- Order manager initialization
- Tradable tickers loading

### Test with Sample Data
```bash
# Test with a small subset of tickers
python -c "
import json
tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
with open('tradable.json', 'w') as f:
    json.dump(tickers, f)
"
python main.py
```

## Safety Features

### Paper Trading
- Default configuration uses paper trading (no real money)
- Set `paper_trading = False` in config.py for live trading
- Always test thoroughly in paper mode first

### Risk Limits
- Maximum 1 active position at a time
- 2% trailing stop loss on all positions
- 5-minute cooldown between trades on same stock
- Automatic filtering of low-quality stocks

### Error Handling
- Graceful handling of API errors
- Automatic reconnection attempts
- Comprehensive logging of all errors
- Safe shutdown on interrupt signals

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure TWS is running and API is enabled
   - Check port number (7497 for paper, 7496 for live)
   - Verify IP is in trusted list or read-only is disabled

2. **No Tradable Tickers**
   - Run `python collect.py` to gather tickers
   - Run `python filter_tickers.py` to filter for IBKR compatibility

3. **API Rate Limits**
   - Polygon API has generous limits for REST calls
   - Bot implements delays to respect rate limits

4. **Memory Usage**
   - Monitor system resources with thousands of threads
   - Consider reducing number of tickers if needed

### Performance Optimization
- Adjust sleep intervals in thread.py for different monitoring frequencies
- Use fewer tickers for testing
- Monitor system resources during operation

## Legal and Risk Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always:

- Test thoroughly in paper trading mode
- Understand the risks involved
- Never risk more than you can afford to lose
- Consult with a financial advisor before live trading
- Comply with all applicable laws and regulations

## License

This project is provided as-is for educational purposes. Use at your own risk.
