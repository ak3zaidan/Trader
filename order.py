from ibapi.contract import Contract
from ibapi.order import Order
from time import sleep
from app import *

class OrderManager:
    def __init__(self, app: TradeApp):
        self.app = app
        self.next_order_id = 1  # simple incremental
        self.app.reqIds(-1)     # ask IBKR for next valid order id

    def _next_id(self):
        oid = self.next_order_id
        self.next_order_id += 1
        return oid

    def _stock_contract(self, symbol: str):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def place_market_order(self, symbol: str, quantity: int):
        oid = self._next_id()
        contract = self._stock_contract(symbol)

        order = Order()
        order.action = "BUY"
        order.orderType = "MKT"
        order.totalQuantity = quantity

        self.app.placeOrder(oid, contract, order)
        return oid

    def place_limit_order(self, symbol: str, quantity: int, limit_price: float):
        oid = self._next_id()
        contract = self._stock_contract(symbol)

        order = Order()
        order.action = "BUY"
        order.orderType = "LMT"
        order.totalQuantity = quantity
        order.lmtPrice = limit_price

        self.app.placeOrder(oid, contract, order)
        return oid

    def place_stop_loss(self, symbol: str, quantity: int, stop_price: float):
        oid = self._next_id()
        contract = self._stock_contract(symbol)

        order = Order()
        order.action = "SELL"
        order.orderType = "STP"
        order.auxPrice = stop_price  # stop trigger
        order.totalQuantity = quantity

        self.app.placeOrder(oid, contract, order)
        return oid

    def place_trailing_stop(self, symbol: str, quantity: int, trail_amount: float):
        oid = self._next_id()
        contract = self._stock_contract(symbol)

        order = Order()
        order.action = "SELL"
        order.orderType = "TRAIL"
        order.totalQuantity = quantity
        order.trailStopPrice = None  # IBKR calculates
        order.auxPrice = trail_amount   # trail amount $

        self.app.placeOrder(oid, contract, order)
        return oid

    def cancel_order(self, order_id: int):
        self.app.cancelOrder(order_id)

    def get_open_orders(self):
        self.app.reqOpenOrders()
        sleep(1)  # give IB time to respond
        return self.app.open_orders

    def get_executions(self):
        self.app.reqExecutions(0, None)
        self.app.order_event.wait(timeout=2)
        return self.app.executions
