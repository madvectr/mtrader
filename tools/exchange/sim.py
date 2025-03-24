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
        
    def generate_limit_price(self, action: str, volatility_scale: float = 1.0) -> float:
        """
        Generate limit order prices based on current price and market conditions.
        Uses exponential distribution to model price distances from current price.
        
        Args:
            action: 'BUY' or 'SELL'
            volatility_scale: Factor to adjust spread width (>1 for volatile markets)
        """
        # Base spread as percentage of price, scaled by volatility
        base_spread = max(0.0001, self.volatility * volatility_scale)
        
        # Generate random distance from current price using exponential distribution
        # Exponential gives more prices near current price, fewer far away
        distance = np.random.exponential(base_spread)
        
        if action == 'BUY':
            # Buy orders typically below current price
            # More aggressive orders (closer to current) are more likely
            price = self.curr_price * (1 - distance)
        else:
            # Sell orders typically above current price
            price = self.curr_price * (1 + distance)
            
        # Round to nearest tick size
        return round(price / self.tick_size) * self.tick_size

    def next_order(self, tick_size: float, tick_time: float) -> Order:
        self.tick_size = tick_size  # Store tick_size for generate_limit_price
        ord_symbol = self.symbol
        if not self.history:
            # initialize market with limit order to add liquidity
            ord_type = 'LIMIT'
        else:
            ord_type = np.random.choice(order_types, p=probabilities)

        # Initialize default values
        ord_price = None
        ord_qty = None
        ord_action = None
        ref_id = None

        if ord_type == 'LIMIT':
            self.update_price(tick_size, tick_time)
            ord_action = np.random.choice(order_action, p=[0.6, 0.4])
            ord_price = self.generate_limit_price(ord_action)
            ord_qty = self.generate_order_size(ord_type)
        elif ord_type == 'MARKET':
            ord_qty = self.generate_order_size(ord_type)
            ord_action = np.random.choice(order_action, p=[0.6, 0.4])
        elif ord_type == 'CANCEL' and self.history:
            ref_id = np.random.choice(list(self.history.keys()))
        elif ord_type == 'MODIFY' and self.history:
            ref_id = np.random.choice(list(self.history.keys()))
            ord_action = np.random.choice(order_action, p=[0.6, 0.4])
            ord_price = self.generate_limit_price(ord_action)
            ord_qty = self.generate_order_size(ord_type)

        order = Order(
            ord_id=str(uuid.uuid4()),
            ref_id=ref_id,
            ord_symbol=ord_symbol,
            ord_type=ord_type,
            ord_price=ord_price,
            ord_qty=ord_qty,
            ord_action=ord_action
        )

        # Add to history if not a CANCEL
        if ord_type != 'CANCEL':
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

def analyze_orders(orders: List[Order]):
    """Analyze order distribution and statistics"""
    type_count = {'LIMIT': 0, 'MARKET': 0, 'CANCEL': 0, 'MODIFY': 0}
    action_count = {'BUY': 0, 'SELL': 0}
    price_points = []
    sizes = []
    
    for order in orders:
        type_count[order.type] += 1
        if order.action:
            action_count[order.action] += 1
        if order.price:
            price_points.append(order.price)
        if order.qty:
            sizes.append(order.qty)
    
    print("\nOrder Analysis:")
    print("Order Types:", {k: f"{v} ({v/len(orders)*100:.1f}%)" for k, v in type_count.items()})
    print("Order Actions:", {k: f"{v} ({v/(action_count['BUY'] + action_count['SELL'])*100:.1f}%)" 
          for k, v in action_count.items()})
    if sizes:
        print(f"Order Sizes - Mean: {np.mean(sizes):.1f}, Median: {np.median(sizes):.1f}, "
              f"Max: {max(sizes)}, Min: {min(sizes)}")
    if price_points:
        print(f"Price Range - Mean: {np.mean(price_points):.2f}, Spread: "
              f"{max(price_points) - min(price_points):.2f}")

def main():
    # Create test instruments
    instruments = [
        Instrument("AAPL", init_price=170.0, volatility=0.0002, drift=0.0001),
        Instrument("MSFT", init_price=280.0, volatility=0.0003, drift=0.0001),
        Instrument("GOOGL", init_price=140.0, volatility=0.0004, drift=0.0002)
    ]
    
    # Initialize exchange
    exchange = Exchange(instruments)
    
    # Run simulation for 1000 ticks
    print("Starting simulation...")
    all_orders = []
    num_ticks = 1000
    
    for tick in range(num_ticks):
        if tick % 100 == 0:
            print(f"Processing tick {tick}")
            # Show current prices
            prices = {inst.symbol: f"{inst.curr_price:.2f}" for inst in instruments}
            print(f"Current Prices: {prices}")
        
        orders = exchange.tick()
        if isinstance(orders, list):
            all_orders.extend(orders)
        else:
            all_orders.append(orders)
    
    # Analyze results per instrument
    print("\nSimulation Complete!")
    for instrument in instruments:
        print(f"\nAnalysis for {instrument.symbol}")
        instrument_orders = [order for order in all_orders 
                           if order.symbol == instrument.symbol]
        analyze_orders(instrument_orders)
        print(f"Final Price: {instrument.curr_price:.2f}")

if __name__ == "__main__":
    main()
