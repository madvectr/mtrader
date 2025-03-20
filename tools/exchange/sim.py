import numpy as np
import json
import uuid

order_types = ['LIMIT', 'MARKET', 'CANCEL', 'MODIFY']
probabilities = [0.7, 0.15, 0.1, 0.05]

order_action = ['BUY', 'SELL']

class Order:
    def __init__(self, ord_id: str, ord_symbol: str, ord_type: str, ord_price: float, ord_qty: int, ord_action: str) -> None:
        self.id = ord_id
        self.symbol = ord_symbol
        self.type = ord_type
        self.price = ord_price
        self.qty = ord_qty
        self.action = ord_action

    def __str__(self) -> str:
        return json.dumps(
            {
                'id': self.id,
                'symbol': self.symbol,
                'type': self.type,
                'price': self.price,
                'qty': self.qty,
                'action': self.action 
            }
        )

class Instrument:
    def __init__(self, symbol: str, init_price: float, volatility: float, drift: float):
        self.curr_price= init_price
        self.symbol = symbol
        self.volatility = volatility
        self.drift = drift
        
    def next_order(self) -> Order:
        ord_type = np.random.choice(order_types, probabilities)
        self.curr_price = self.curr_price * self.volatility + self.drift
        return Order(
            ord_id=uuid.uuid4(),
            ord_symbol=self.symbol,
            ord_type=ord_type,
            ord_price=self.curr_price,
            ord_action=np.random.choice(order_action, [0.6, 0.4])
        )

