from ibapi.contract import Contract
from app import TradeApp
from utils import *

class MarketData:
    def __init__(self, app: TradeApp):
        self.app = app
        self.req_id = 0

    def _next_req_id(self):
        self.req_id += 1
        return self.req_id

    def _create_contract(self, symbol, sec_type="STK", exchange="SMART", currency="USD"):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract

    def get_historical_data(self, symbol, interval: Interval):
        req_id = self._next_req_id()
        contract = self._create_contract(symbol)

        self.app.data_end_event.clear()
        self.app.reqHistoricalData(
            reqId=req_id,
            contract=contract,
            endDateTime="",
            durationStr=interval.duration,
            barSizeSetting=interval.bar_size,
            whatToShow="TRADES",
            useRTH=0,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )

        # wait until data ends
        self.app.data_end_event.wait(timeout=15)
        bars = self.app.historical_data.pop(req_id, [])
        return bars

    def is_tradable(self, symbol: str) -> bool:
        """
        Check if a given stock symbol is tradable on IBKR.
        Only returns True for normal US stocks (secType='STK', currency='USD').
        """
        req_id = self._next_req_id()
        contract = self._create_contract(symbol, sec_type="STK", exchange="SMART", currency="USD")

        self.app.contract_details_event.clear()
        self.app.reqContractDetails(req_id, contract)

        # wait until details return
        self.app.contract_details_event.wait(timeout=5)
        details = self.app.contract_details.pop(req_id, [])

        # If no contract details, it's not tradable
        if not details:
            print("Failed to fetch details")
            return False

        # Ensure it's a normal stock (STK, USD, US exchange)
        for d in details:
            c = d.contract
            
            if (c.secType == "STK" and c.currency == "USD"):
                return True

        return False
