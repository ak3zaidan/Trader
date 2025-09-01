# IBKR config
paper_trading = True
host = "127.0.0.1"
port = 7497
client_id = 0

# Polygon config
polygon_api_key = "CpZj6msyprLmcgjcsDABdog6B1OBdHtj"

# Volume check
max_volume_percent = 0.001
volume_price_ratio = 1000 # How many times larger than the current price is the volume

# Trading config
account_value = 25000
trade_size_percent = 100.0 # 100% of account value
minutes_exit_fast_mode = 20 # Exit fast mode if the stock has not gained +5% in this many minutes
