from decimal import Decimal
from app.domain.order import Order,OrderType
from app.domain.exceptions import InsufficientFundsError, InsufficientHoldingsError
class Account():
    def __init__(self,balance:Decimal,id:int):
        self.id=id
        self.balance=balance
        self.holdings={}

    def place_order(self,order:Order,current_market_price:Decimal)->str:
        if not  order.can_execute(current_market_price):
            return "Order Pending"
        symbol = order.asset.symbol
        total_cost = order.quantity * current_market_price
        if order.order_type== OrderType.BUY:
            if total_cost > self.balance:
                raise InsufficientFundsError("Insufficient funds to execute the order.")
            self.balance -= total_cost
            if symbol in self.holdings:
                new_avg_price = (self.holdings[symbol]["avg_price"] * self.holdings[symbol]["quantity"] + current_market_price * order.quantity) / (self.holdings[symbol]["quantity"] + order.quantity)
                self.holdings[symbol]["quantity"] = self.holdings[symbol]["quantity"] + order.quantity
                self.holdings[symbol]["avg_price"] = new_avg_price
            else:
                self.holdings[symbol] = {"quantity": order.quantity, "avg_price": Decimal(current_market_price), "asset":order.asset}
        elif order.order_type == OrderType.SELL:
            if symbol not in self.holdings or self.holdings[symbol]["quantity"] < order.quantity:
                raise InsufficientHoldingsError("Insufficient holdings to execute the sell order.")
            self.balance += total_cost
            self.holdings[symbol]["quantity"] -= order.quantity
            if self.holdings[symbol]["quantity"] == 0:
                del self.holdings[symbol]
        return f"Order executed: {order.order_type.value} {order.quantity} of {order.asset.symbol} at {current_market_price}"

    
