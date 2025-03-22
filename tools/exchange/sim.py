import numpy as np
import json
import uuid
from typing import Dict, List

order_types = ['LIMIT', 'MARKET', 'CANCEL', 'MODIFY']
probabilities = [0.7, 0.15, 0.1, 0.05]

order_action = ['BUY', 'SELL']

class Order:
    """
    Order class to represent an order in the exchange.
    """
    def __init__(
            self, ord_id: str, 
            ref_id: str, 
            ord_symbol: str, 
            ord_type: str, 
            ord_price: float, 
            ord_qty: int, 
            ord_action: str) -> None:

        # Structure based on the order type
        # LIMIT: ord_id, ref_id, symbol, type, price, qty, action
        # MARKET: ord_id, ref_id, symbol, type, qty, action
        # CANCEL: ord_id, ref_id, symbol, type
        # MODIFY: ord_id, ref_id, symbol, type, price, qty
        # ref_id is the id of the order that this order is modifying or cancelling

        self.id = ord_id
        self.ref_id = ref_id
        self.symbol = ord_symbol
        self.type = ord_type
        self.price = ord_price
        self.qty = ord_qty
        self.action = ord_action

    def __str__(self) -> str:
        
        # Base for CANCEL orders
        order_dict = {
            'id': self.id,
            'ref_id': self.ref_id,
            'symbol': self.symbol,
            'type': self.type,
        }

        if self.type == 'LIMIT':
            order_dict['price'] = self.price
            order_dict['qty'] = self.qty
            order_dict['action'] = self.action
        elif self.type == 'MARKET':
            order_dict['qty'] = self.qty
            order_dict['action'] = self.action
        elif self.type == 'MODIFY':
            order_dict['price'] = self.price
            order_dict['qty'] = self.qty

        return json.dumps(order_dict)

class Instrument:
    """
    Instrument class to represent an instrument in the exchange.
    """
    def __init__(self, symbol: str, init_price: float, volatility: float = 1.0, drift: float = 0.01):
        self.curr_price= init_price
        self.symbol = symbol
        self.volatility = volatility
        self.drift = drift
        self.history : Dict[str, Order] = {}

    def update_price(self, tick_size: float, tick_time: float):
        # Using Markovian style Brownian motion with drift
        scaled_vol = self.volatility * np.sqrt(tick_time)
        scaled_drift = self.drift * tick_time
        price_change = np.random.normal(0, 1) * scaled_vol + scaled_drift
        new_price = self.curr_price + price_change
        self.curr_price = round(new_price/tick_size) * tick_size
        
    def next_order(self, tick_size: float, tick_time: float) -> Order:
        ord_symbol = self.symbol
        if not self.history:
            # initialize market with limit order to add liquidity
            ord_type = 'LIMIT'
        else:
            ord_type = np.random.choice(order_types, probabilities)

        if ord_type == 'LIMIT':
            self.update_price(tick_size, tick_time) 
            ord_price = self.curr_price
            ord_action = np.random.choice(order_action, [0.6, 0.4])
            ord_qty = self.generate_order_size(ord_type)
        elif ord_type == 'MARKET':
            ord_qty = self.generate_order_size(ord_type)
            ord_action = np.random.choice(order_action, [0.6, 0.4])
        elif ord_type == 'CANCEL':
            ref_id = np.random.choice(list(self.history.keys()))
        elif ord_type == 'MODIFY':
            self.update_price(tick_size, tick_time)
            ord_price = self.curr_price
            ref_id = np.random.choice(list(self.history.keys()))
            ord_action = np.random.choice(order_action, [0.6, 0.4])
            ord_qty = self.generate_order_size(ord_type)

        if ord_type == 'MODIFY': 
            ref_id = np.random.choice(list(self.history.keys()))
        else:
            ref_id = None

        order = Order(
            ord_id=uuid.uuid4(),
            ref_id=ref_id,
            ord_symbol=ord_symbol,
            ord_type=ord_type,
            ord_price=ord_price,
            ord_qty=ord_qty,
            ord_action=ord_action
        )

        # Add order to history
        self.history[order.id] = order

        return order

    def tick(self, tick_size: float, tick_time: float) -> Order:
        self.tick_count += 1
        return self.next_order(tick_size, tick_time)

    def generate_order_size(self, ord_type: str, base_size: float = 100) -> int:
        if ord_type == 'MARKET':
            # Market orders: larger sizes, less variance
            mu = np.log(base_size) + 0.5  # centers around 150-200
            sigma = 0.8  # tighter distribution
        else:
            # Limit orders: smaller sizes, more variance
            mu = np.log(base_size)  # centers around 100
            sigma = 1.2  # wider distribution
        
        size = int(np.random.lognormal(mu, sigma))
        return max(1, min(size, base_size * 10))  # Cap size between 1 and 1000 for base_size=100
        
class Exchange:
    """
    Exchange class to represent an exchange in the exchange.
    """
    def __init__(self, instruments: List[Instrument]):
        self.instruments: List[Instrument] = instruments
        self.tick_size = 0.01
        self.tick_time = 0.01
        self.tick_count = 0
        self.history: Dict[str, Order] = {}

    def tick(self) -> Order:
        for instrument in self.instruments:
            order = instrument.tick(self.tick_size, self.tick_time)
            self.history[order.id] = order
        return order
