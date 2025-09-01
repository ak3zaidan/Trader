from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from threading import Event, Lock
from datetime import datetime
from ibapi.common import *
import time

class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

        # Connection state
        self.connected = False
        self.next_valid_order_id = None
        self.connection_lock = Lock()

        # Events for different request types
        self.historical_data_event = Event()
        self.contract_details_event = Event()
        self.order_event = Event()
        self.account_event = Event()
        self.position_event = Event()
        self.next_valid_id_event = Event()

        # Storage for results
        self.historical_data = {}
        self.contract_details = {}
        self.open_orders = {}
        self.executions = {}
        self.positions = {}
        self.account_info = {}
        
        # Thread safety
        self.data_lock = Lock()

    # Connection management
    def connect_and_run(self, host, port, client_id):
        """Connect to TWS and start the message loop"""
        try:
            self.connect(host, port, client_id)
            self.connected = True
            print(f"✅ Connected to TWS on {host}:{port}")
            
            # Start the message loop in a separate thread
            import threading
            self.msg_thread = threading.Thread(target=self.run, daemon=True)
            self.msg_thread.start()
            
            # Wait for connection to be fully established
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to TWS: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from TWS"""
        if self.connected:
            self.disconnect()
            self.connected = False
            print("✅ Disconnected from TWS")

    def is_connected(self):
        """Check if connected to TWS"""
        return self.connected

    # Next valid order ID
    def nextValidId(self, orderId):
        """Callback for next valid order ID"""
        with self.connection_lock:
            self.next_valid_order_id = orderId
            self.next_valid_id_event.set()
        print(f"✅ Next valid order ID: {orderId}")

    def get_next_order_id(self):
        """Get the next valid order ID"""
        if self.next_valid_order_id is None:
            # Request next valid ID if not available
            self.reqIds(-1)
            self.next_valid_id_event.wait(timeout=5)
        
        if self.next_valid_order_id is not None:
            order_id = self.next_valid_order_id
            self.next_valid_order_id += 1
            return order_id
        else:
            raise Exception("Could not get next valid order ID")

    # Account information
    def updateAccountValue(self, key, val, currency, accountName):
        """Callback for account value updates"""
        with self.data_lock:
            if accountName not in self.account_info:
                self.account_info[accountName] = {}
            self.account_info[accountName][key] = {
                'value': val,
                'currency': currency
            }
        self.account_event.set()

    def accountDownloadEnd(self, accountName):
        """Callback when account download is complete"""
        print(f"✅ Account download completed for {accountName}")

    def get_account_info(self, account_name=None):
        """Get account information"""
        with self.data_lock:
            if account_name:
                return self.account_info.get(account_name, {})
            return self.account_info

    # Position tracking
    def position(self, account, contract, pos, avgCost):
        """Callback for position updates"""
        with self.data_lock:
            symbol = contract.symbol
            self.positions[symbol] = {
                'account': account,
                'contract': contract,
                'position': pos,
                'avgCost': avgCost,
                'timestamp': datetime.now()
            }
        self.position_event.set()

    def positionEnd(self):
        """Callback when position download is complete"""
        print(f"✅ Position download completed. {len(self.positions)} positions loaded")

    def get_positions(self):
        """Get all current positions"""
        with self.data_lock:
            return self.positions.copy()

    def get_position(self, symbol):
        """Get position for a specific symbol"""
        with self.data_lock:
            return self.positions.get(symbol)

    # Contract details callbacks
    def contractDetails(self, reqId, contractDetails):
        with self.data_lock:
            if reqId not in self.contract_details:
                self.contract_details[reqId] = []
            self.contract_details[reqId].append(contractDetails)

    def contractDetailsEnd(self, reqId):
        self.contract_details_event.set()

    # Historical data callbacks
    def historicalData(self, reqId, bar):
        with self.data_lock:
            if reqId not in self.historical_data:
                self.historical_data[reqId] = []
            self.historical_data[reqId].append(bar)

    def historicalDataEnd(self, reqId, start, end):
        self.historical_data_event.set()

    # Order callbacks
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        with self.data_lock:
            self.open_orders[orderId] = dict(
                status=status,
                filled=filled,
                remaining=remaining,
                avgFillPrice=avgFillPrice,
                lastFillPrice=lastFillPrice,
                permId=permId,
                parentId=parentId,
                whyHeld=whyHeld,
                timestamp=datetime.now()
            )
        self.order_event.set()
        
        # Log order status changes
        print(f"📊 Order {orderId}: {status} - Filled: {filled}, Remaining: {remaining}")

    def openOrder(self, orderId, contract, order, orderState):
        with self.data_lock:
            self.open_orders[orderId] = dict(
                symbol=contract.symbol,
                action=order.action,
                totalQuantity=order.totalQuantity,
                orderType=order.orderType,
                status=orderState.status,
                lmtPrice=getattr(order, 'lmtPrice', None),
                auxPrice=getattr(order, 'auxPrice', None),
                timestamp=datetime.now()
            )
        self.order_event.set()

    def execDetails(self, reqId, contract, execution):
        with self.data_lock:
            self.executions[execution.execId] = dict(
                symbol=contract.symbol,
                side=execution.side,
                shares=execution.shares,
                price=execution.price,
                time=execution.time,
                account=execution.acctNumber,
                timestamp=datetime.now()
            )
        self.order_event.set()
        
        # Log executions
        print(f"💰 Execution: {contract.symbol} {execution.side} {execution.shares} @ ${execution.price}")

    # Enhanced error handling
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """Enhanced error handling with specific error codes"""
        
        # Log all errors
        if reqId == -1:
            # System messages
            print(f"ℹ️  System: {errorString}")
        else:
            print(f"❌ Error {reqId} {errorCode}: {errorString}")

        # Handle specific error codes
        if errorCode == 1100:  # Connectivity between IB and TWS lost
            print("🔌 Connection lost between IB and TWS")
            self.connected = False
        elif errorCode == 1101:  # Connectivity restored
            print("🔌 Connection restored")
            self.connected = True
        elif errorCode == 1102:  # TWS API connection lost
            print("🔌 TWS API connection lost")
            self.connected = False
        elif errorCode == 2104:  # Market data farm connection is OK
            print("📊 Market data connection OK")
        elif errorCode == 2106:  # HMDS data farm connection is OK
            print("📊 HMDS data connection OK")
        elif errorCode == 2158:  # Sec-def data farm connection is OK
            print("📊 Sec-def data connection OK")
        elif errorCode == 10182:  # Duplicate order ID
            print("⚠️  Duplicate order ID - requesting new ID")
            self.reqIds(-1)
        elif errorCode == 10187:  # Order cancelled
            print("❌ Order cancelled")
        elif errorCode == 10189:  # Order rejected
            print("❌ Order rejected")
        elif errorCode == 10190:  # Order replaced
            print("✅ Order replaced")
        elif errorCode == 10191:  # Order filled
            print("✅ Order filled")
        elif errorCode == 10192:  # Order partially filled
            print("⚠️  Order partially filled")
        elif errorCode == 10193:  # Order submitted
            print("📤 Order submitted")
        elif errorCode == 10194:  # Order pending submit
            print("⏳ Order pending submit")
        elif errorCode == 10195:  # Order pre-submitted
            print("📋 Order pre-submitted")
        elif errorCode == 10196:  # Order cancelled
            print("❌ Order cancelled")
        elif errorCode == 10197:  # Order inactive
            print("⏸️  Order inactive")
        elif errorCode == 10198:  # Order unknown
            print("❓ Order unknown")
        elif errorCode == 10199:  # Order held
            print("⏸️  Order held")

        # Unblock waiting threads for specific errors
        if reqId in self.contract_details or errorCode == 200:  # contract detail error
            self.contract_details_event.set()
        if reqId in self.historical_data or errorCode in (162, 200):  # historical data error
            self.historical_data_event.set()
        if errorCode in (10187, 10189, 10190, 10191, 10192, 10193, 10194, 10195, 10196, 10197, 10198, 10199):  # order errors
            self.order_event.set()

    # Utility methods
    def clear_data(self):
        """Clear all stored data"""
        with self.data_lock:
            self.historical_data.clear()
            self.contract_details.clear()
            self.open_orders.clear()
            self.executions.clear()
            self.positions.clear()
            self.account_info.clear()

    def get_order_status(self, order_id):
        """Get status of a specific order"""
        with self.data_lock:
            return self.open_orders.get(order_id)

    def get_execution(self, exec_id):
        """Get details of a specific execution"""
        with self.data_lock:
            return self.executions.get(exec_id)

    def wait_for_order_fill(self, order_id, timeout=60):
        """Wait for an order to be filled"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            order_status = self.get_order_status(order_id)
            if order_status and order_status['status'] in ['Filled', 'Cancelled']:
                return order_status
            time.sleep(0.1)
        return None

    def get_account_summary(self):
        """Get a summary of account information"""
        with self.data_lock:
            summary = {}
            for account, data in self.account_info.items():
                summary[account] = {}
                for key, value in data.items():
                    if key in ['NetLiquidation', 'TotalCashValue', 'AvailableFunds', 'BuyingPower']:
                        summary[account][key] = value
            return summary

    def request_account_info(self):
        """Request account information from TWS"""
        self.reqAccountUpdates(True, "")
        print("📊 Requested account information")

    def request_positions(self):
        """Request current positions from TWS"""
        self.reqPositions()
        print("📊 Requested current positions")

    def cancel_all_orders(self):
        """Cancel all open orders"""
        self.reqGlobalCancel()
        print("❌ Cancelled all open orders")

    def get_open_orders_count(self):
        """Get count of open orders"""
        with self.data_lock:
            return len(self.open_orders)

    def get_active_positions_count(self):
        """Get count of active positions"""
        with self.data_lock:
            return len([pos for pos in self.positions.values() if pos['position'] != 0])

    def is_market_open(self):
        """Check if market is currently open (simplified check)"""
        now = datetime.now()
        # US market hours: 9:30 AM - 4:00 PM ET (simplified)
        # This is a basic check - for production, use proper market calendar
        if now.weekday() < 5:  # Monday to Friday
            hour = now.hour
            if 9 <= hour < 16:  # 9 AM to 4 PM
                return True
        return False

    def get_connection_status(self):
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'next_order_id': self.next_valid_order_id,
            'open_orders': self.get_open_orders_count(),
            'positions': self.get_active_positions_count(),
            'market_open': self.is_market_open()
        }
