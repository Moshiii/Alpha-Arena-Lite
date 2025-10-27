"""
Simple example: Update portfolio with live market data every tick
"""
from simple_portfolio import SimplePortfolio, Position
from hyperliquid_market_data import get_last_price_from_hyperliquid
import time


def main():
    # Create or load portfolio
    portfolio = SimplePortfolio()
    
    # Try to load existing portfolio
    try:
        portfolio.load_from_file("portfolio.json")
        print("Loaded existing portfolio")
    except FileNotFoundError:
        print("Creating new portfolio with sample positions")
        # Add some positions
        portfolio.add_position(Position(
            symbol="BTC",
            quantity=0.5,
            entry_price=45000.0,
            liquidation_price=40000.0,
            leverage=10.0
        ))
        
        portfolio.add_position(Position(
            symbol="ETH",
            quantity=-10.0,  # Short position
            entry_price=3000.0,
            leverage=5.0
        ))
    
    # Update loop - fetch latest prices and update
    print("\nUpdating prices from Hyperliquid...\n")
    
    for i in range(3):  # Run 3 updates as example
        print(f"--- Update {i+1} ---")
        
        # Get symbols we're tracking
        symbols = list(portfolio.positions.keys())
        
        # Fetch latest prices
        price_updates = {}
        for symbol in symbols:
            price = get_last_price_from_hyperliquid(symbol)
            if price:
                price_updates[symbol] = price
        
        # Update all positions with latest prices
        if price_updates:
            portfolio.update_all_prices(price_updates)
            
            # Display
            portfolio.display()
            
            # Save to JSON after update
            portfolio.save_to_file("portfolio.json")
        
        # Wait before next update
        if i < 2:
            time.sleep(5)


if __name__ == "__main__":
    main()

