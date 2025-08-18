from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from threading import Event

class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

        # Events for different request types
        self.historical_data_event = Event()
        self.contract_details_event = Event()
        self.order_event = Event()

        # Storage for results
        self.historical_data = {}
        self.contract_details = {}
        self.open_orders = {}
        self.executions = {}

    # -------------------------
    # Contract details callbacks
    # -------------------------
    def contractDetails(self, reqId, contractDetails):
        if reqId not in self.contract_details:
            self.contract_details[reqId] = []
        self.contract_details[reqId].append(contractDetails)

    def contractDetailsEnd(self, reqId):
        self.contract_details_event.set()

    # -------------------------
    # Historical data callbacks
    # -------------------------
    def historicalData(self, reqId, bar):
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append(bar)

    def historicalDataEnd(self, reqId, start, end):
        self.historical_data_event.set()

    # -------------------------
    # Order callbacks
    # -------------------------
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        self.open_orders[orderId] = dict(
            status=status,
            filled=filled,
            remaining=remaining,
            avgFillPrice=avgFillPrice,
            lastFillPrice=lastFillPrice
        )
        self.order_event.set()

    def openOrder(self, orderId, contract, order, orderState):
        self.open_orders[orderId] = dict(
            symbol=contract.symbol,
            action=order.action,
            totalQuantity=order.totalQuantity,
            orderType=order.orderType,
            status=orderState.status
        )
        self.order_event.set()

    def execDetails(self, reqId, contract, execution):
        self.executions[execution.execId] = dict(
            symbol=contract.symbol,
            side=execution.side,
            shares=execution.shares,
            price=execution.price,
            time=execution.time
        )
        self.order_event.set()

    # -------------------------
    # Generic error handling
    # -------------------------
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"ERROR {reqId} {errorCode} {errorString}")

        # If the error relates to a request that waits on an Event, unblock it immediately
        if reqId in self.contract_details or errorCode == 200:  # contract detail error
            self.contract_details_event.set()
        if reqId in self.historical_data or errorCode in (162, 200):  # historical data error
            self.historical_data_event.set()
        # You can add more cases for orders if needed
