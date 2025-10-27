"""
Simple Portfolio Tracker - One position per symbol
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime


class Position:
    """Simple position tracking - one per symbol"""
    
    def __init__(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        current_price: float = None,
        liquidation_price: Optional[float] = None,
        leverage: float = 1.0,
        profit_target: Optional[float] = None,
        stop_loss: Optional[float] = None,
        confidence: float = 0.5
    ):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.current_price = current_price or entry_price
        self.liquidation_price = liquidation_price
        self.leverage = leverage
        self.entry_time = datetime.now().isoformat()
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.confidence = confidence
        
    def calculate_liquidation_price(self) -> float:
        """Calculate liquidation price"""
        # Double check: Correct liquidation price for long/short with leverage is:
        return self.entry_price * (1 - 1/self.leverage)
    
    def calculate_unrealized_pnl(self) -> float:
        """Calculate unrealized PnL with leverage"""
        direction = 1 if self.quantity >= 0 else -1
        return (self.current_price - self.entry_price) * abs(self.quantity) * self.leverage * direction

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'liquidation_price': self.liquidation_price,
            'leverage': self.leverage,
            'unrealized_pnl': self.calculate_unrealized_pnl(),
            'entry_time': self.entry_time
        }
    
    def calculate_risk_usd(self) -> float:
        """Calculate risk in USD (distance to stop loss)"""
        if self.stop_loss is None:
            return 0.0
        direction = 1 if self.quantity >= 0 else -1
        return abs(self.entry_price - self.stop_loss) * abs(self.quantity) * self.leverage
    
    def calculate_notional_usd(self) -> float:
        """Calculate notional value in USD"""
        return abs(self.quantity) * self.current_price
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON format as requested"""
        # Calculate exit plan
        exit_plan = {}
        if self.profit_target is not None:
            exit_plan['profit_target'] = self.profit_target
        if self.stop_loss is not None:
            exit_plan['stop_loss'] = self.stop_loss
        
        # Calculate invalidation condition if stop_loss exists
        if self.stop_loss is not None:
            invalidation_level = self.stop_loss
            exit_plan['invalidation_condition'] = f"If the price closes below {invalidation_level:.2f} on a 3-minute candle"
        
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'liquidation_price': self.liquidation_price,
            'unrealized_pnl': self.calculate_unrealized_pnl(),
            'leverage': self.leverage,
            'exit_plan': exit_plan,
            'confidence': self.confidence,
            'risk_usd': self.calculate_risk_usd(),
            'notional_usd': self.calculate_notional_usd()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """Create from dictionary"""
        return cls(
            symbol=data['symbol'],
            quantity=data['quantity'],
            entry_price=data['entry_price'],
            current_price=data.get('current_price', data['entry_price']),
            liquidation_price=data.get('liquidation_price'),
            leverage=data.get('leverage', 1.0),
            profit_target=data.get('profit_target'),
            stop_loss=data.get('stop_loss'),
            confidence=data.get('confidence', 0.5)
        )


class SimplePortfolio:
    """Super simple portfolio - one position per symbol"""
    
    def __init__(self, initial_cash: float = 10000.0):
        self.positions: Dict[str, Position] = {}
        self.initial_cash = initial_cash
        self.available_cash = initial_cash
        self.total_asset = initial_cash
    
    def add_position(self, position: Position) -> None:
        """Add or replace position for a symbol"""
        # Calculate collateral needed for this position
        collateral_needed = abs(position.quantity) * position.entry_price / position.leverage
        
        # Check if we already have this position to handle collateral
        old_collateral = 0
        if position.symbol in self.positions:
            old_position = self.positions[position.symbol]
            old_collateral = abs(old_position.quantity) * old_position.entry_price / old_position.leverage
        
        # Update available cash
        self.available_cash = self.available_cash + old_collateral - collateral_needed
        
        # Add position
        self.positions[position.symbol] = position
        
        # Update total asset
        self._update_total_asset()
    
    def add_order(self, symbol: str, quantity: float, price: float, leverage: float = 1.0, 
                  profit_target: Optional[float] = None, stop_loss: Optional[float] = None,
                  confidence: float = 0.5) -> bool:
        """Add a new order - creates a position and calculates additional attributes
        
        If existing position has opposite sign, closes the position first.
        
        Returns:
            True if order was added successfully
            False if position already exists for this symbol with same direction
        """
        # Check if position already exists for this symbol
        if symbol in self.positions and self.positions[symbol].quantity != 0:
            existing_quantity = self.positions[symbol].quantity
            
            # Check if we're trying to close the position (opposite signs)
            if (existing_quantity > 0 and quantity < 0) or (existing_quantity < 0 and quantity > 0):
                print(f"Closing existing {symbol} position (Qty: {existing_quantity:.4f})")
                # Close the existing position
                self.remove_position(symbol)
                # Continue to add the new position below
            elif existing_quantity == 0:
                # Empty position exists, just update it
                pass
            else:
                print(f"Position already exists for {symbol} with same direction, cannot add order")
                return False
        
        print(f"Adding position for {symbol} (Qty: {quantity:.4f})")
        
        # Calculate liquidation price
        liquidation_price = price * (1 - 1/leverage) if leverage > 1 else None
        
        # Create position with all calculated attributes
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            current_price=price,
            liquidation_price=liquidation_price,
            leverage=leverage,
            profit_target=profit_target,
            stop_loss=stop_loss,
            confidence=confidence
        )
        
        # Add position to portfolio
        self.add_position(position)
        return True
    
    def remove_position(self, symbol: str) -> None:
        """Remove a position"""
        if symbol in self.positions:
            position = self.positions[symbol]
            # Return collateral to available cash
            collateral = abs(position.quantity) * position.entry_price / position.leverage
            unrealized_pnl = position.calculate_unrealized_pnl()
            # When closing position, we get back collateral + unrealized PnL
            self.available_cash += collateral + unrealized_pnl
        self.positions.pop(symbol, None)
        # Update total asset
        self._update_total_asset()
    
    def update_price(self, symbol: str, new_price: float) -> None:
        """Update current price for a position"""
        if symbol in self.positions:
            self.positions[symbol].current_price = new_price
            self._update_total_asset()
    
    def update_unrealized_pnl(self, symbol: str) -> None:
        """Update PnL for a position"""
        if symbol in self.positions:
            self.positions[symbol].unrealized_pnl = self.positions[symbol].calculate_unrealized_pnl()
    
    def update_all_prices(self, price_updates: Dict[str, float]) -> None:
        """Update prices for multiple positions at once"""
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price
        self._update_total_asset()
    
    def _recalculate_assets(self) -> None:
        """Recalculate available cash and total asset based on current positions"""
        # Calculate total collateral used
        total_collateral = 0
        for position in self.positions.values():
            collateral = abs(position.quantity) * position.entry_price / position.leverage
            total_collateral += collateral
        
        # Available cash = initial cash - collateral used
        self.available_cash = self.initial_cash - total_collateral
        
        # Update total asset
        self._update_total_asset()
    
    def _update_total_asset(self) -> None:
        """Calculate and update total asset value"""
        # Total asset = available cash + (collateral + unrealized PnL for each position)
        position_values = 0
        for position in self.positions.values():
            collateral = abs(position.quantity) * position.entry_price / position.leverage
            unrealized_pnl = position.calculate_unrealized_pnl()
            position_values += collateral + unrealized_pnl
        
        self.total_asset = self.available_cash + position_values
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        return list(self.positions.values())
    
    def total_pnl(self) -> float:
        """Calculate total PnL across all positions"""
        return sum(pos.calculate_unrealized_pnl() for pos in self.positions.values())
    
    def save_to_file(self, filename: str) -> None:
        """Save portfolio to JSON file"""
        data = {
            'positions': [pos.to_dict() for pos in self.positions.values()],
            'timestamp': datetime.now().isoformat(),
            'initial_cash': self.initial_cash,
            'available_cash': self.available_cash,
            'total_asset': self.total_asset
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filename: str) -> None:
        """Load portfolio from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Load cash information if available
        self.initial_cash = data.get('initial_cash', self.initial_cash)
        self.available_cash = data.get('available_cash', self.initial_cash)
        
        self.positions = {}
        for pos_data in data.get('positions', []):
            position = Position.from_dict(pos_data)
            self.positions[position.symbol] = position
        
        # Recalculate available cash and total asset
        self._recalculate_assets()
    
    def display(self) -> None:
        """Simple display of all positions"""
        if not self.positions:
            print("No positions")
            return
        
        print(f"\n{'Symbol':<10} {'Qty':<10} {'Entry':<10} {'Current':<10} {'PnL':<10} {'Leverage':<10}")
        print("-" * 70)
        
        for pos in self.positions.values():
            pnl = pos.calculate_unrealized_pnl()
            pnl_str = f"${pnl:.4f}"
            print(f"{pos.symbol:<10} {pos.quantity:<10.4f} ${pos.entry_price:<9.2f} ${pos.current_price:<9.2f} {pnl_str:<10} {pos.leverage}x")
        
        print("-" * 70)
        print(f"Total PnL: ${self.total_pnl():.4f}")
        print(f"Available Cash: ${self.available_cash:.4f}")
        print(f"Total Asset: ${self.total_asset:.4f}\n")
    def return_json(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Return portfolio data in JSON format
        
        Args:
            symbol: Optional symbol to return data for. If None, returns all positions.
        
        Returns:
            If symbol is provided: single position JSON
            If symbol is None: dict with all positions as list
        """
        if symbol:
            if symbol not in self.positions:
                return {}
            return self.positions[symbol].to_json()
        
        # Return all positions as a list
        return {
            'positions': [pos.to_json() for pos in self.positions.values()],
            'timestamp': datetime.now().isoformat(),
            'total_pnl': self.total_pnl(),
            'available_cash': self.available_cash,
            'total_asset': self.total_asset,
            'initial_cash': self.initial_cash
        }
    def to_string(self, json_result: Dict[str, Any]) -> str:
        """Convert portfolio JSON to formatted string"""
        result_string = "HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE\n"
        
        # Calculate total return
        initial_cash = json_result.get('initial_cash', 10000.0)
        total_asset = json_result.get('total_asset', 0)
        total_return = ((total_asset - initial_cash) / initial_cash) * 100 if initial_cash > 0 else 0
        
        result_string += f"Current Total Return (percent): {total_return:.2f}%\n"
        result_string += f"Available Cash: {json_result.get('available_cash', 0):.2f}\n"
        result_string += f"Current Account Value: {total_asset:.2f}\n"
        result_string += "Current live positions & performance:\n\n"
        
        # Display each position
        positions = json_result.get('positions', [])
        for pos in positions:
            result_string += f"{pos}\n"
        
        return result_string

# Example usage
if __name__ == "__main__":
    # Create portfolio
    portfolio = SimplePortfolio()
    
    # Add positions using add_order
    portfolio.add_order("BTC", quantity=0.5, price=45000.0, leverage=10.0)
    portfolio.add_order("ETH", quantity=-10.0, price=3000.0, leverage=5.0)
    
    # Update current prices
    portfolio.update_all_prices({
        "BTC": 45500.0,
        "ETH": 2950.0
    })
    
    # Display
    portfolio.display()
    
    # Update prices
    portfolio.update_all_prices({
        "BTC": 46000.0,
        "ETH": 2920.0
    })
    
    portfolio.display()
    
    # Save
    portfolio.save_to_file("portfolio.json")

