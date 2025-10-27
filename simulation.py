"""
Simple Market Data Simulation - Buy positions and update portfolio every loop
"""
import time
import json
from datetime import datetime
from hyperliquid_market_data import get_last_price_from_hyperliquid, symbol_data_provider_json, to_string
from simple_portfolio import SimplePortfolio, Position
# from trade_decision_rule_based import trade_decision_provider
# from trade_decision_simple import trade_decision_provider
from trade_decision_simple_AI import trade_decision_provider

# Track these symbols
SYMBOLS = ['BTC', 'ETH', 'SOL']
PORTFOLIO_FILE = 'portfolio.json'
BUY_QUANTITY = 0.0001  # Buy this amount each loop


# Load or create portfolio
portfolio = SimplePortfolio()

try:
    portfolio.load_from_file('portfolio_init.json')
    print("Loaded existing portfolio")
    print(f"Initial Cash: ${portfolio.initial_cash:,.2f}")
    print(f"Available Cash: ${portfolio.available_cash:,.2f}")
    portfolio.display()
except FileNotFoundError:
    print("Creating new portfolio")
    print(f"Initial Cash: ${portfolio.initial_cash:,.2f}")

loop_count = 0

while True:
    loop_count += 1
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - Loop #{loop_count} - Fetching market data...")
    
    market_data_for_decisions_json = {}
    market_data_for_decisions_string = ""
    
    for symbol in SYMBOLS:
        price = get_last_price_from_hyperliquid(symbol)
        json_result = symbol_data_provider_json(symbol, '3m', 10)
        
        # Add symbol and frequency to json_result for to_string
        json_result['symbol'] = symbol
        json_result['frequency'] = '3m'
        market_data_string = to_string(json_result)
        print(market_data_string)
        
        print(f"{symbol}: ${price:,.2f}")
        if price:     
            portfolio.update_price(symbol, price)
            portfolio.update_unrealized_pnl(symbol)
        
        # Store market data for later use in trade decisions
        market_data_for_decisions_json[symbol] = json_result
        market_data_for_decisions_string += market_data_string + "\n"
        
    # Update portfolio prices and display
    portfolio.display()
    portfolio_json = portfolio.return_json()
    portfolio_string = portfolio.to_string(portfolio_json)
    print("\n📊 Portfolio Status:")
    print(portfolio_string)
    
    # Generate trading decisions
    print("\n📊 Generating Trading Decisions...")
    all_decisions = trade_decision_provider(market_data_for_decisions_json, portfolio_json)
    
    # Print the trading decisions
    print("\n" + "="*80)
    if all_decisions:
        for symbol, decision_data in all_decisions.items():
            args = decision_data["trade_signal_args"]
            print(f"\n{symbol} Trading Decision:")
            print(f"  Signal: {args['signal']}")
            print(f"  Quantity: {args['quantity']}")
            print(f"  Entry Price: ${args.get('entry_price', 0):.2f}")
            print(f"  Profit Target: ${args['profit_target']}")
            print(f"  Stop Loss: ${args['stop_loss']}")
            print(f"  Leverage: {args['leverage']}x")
            print(f"  Confidence: {args['confidence']}")
            print(f"  Risk: ${args['risk_usd']}")
            print(f"  Invalidation: {args['invalidation_condition']}")
        
        # Execute orders based on decisions
        print("\n📝 Executing Orders...")
        for symbol, decision_data in all_decisions.items():
            args = decision_data["trade_signal_args"]
            
            # Check if we have sufficient cash
            collateral_needed = abs(args['quantity']) * args.get('entry_price', 0) / args['leverage']
            if collateral_needed > portfolio.available_cash:
                print(f"❌ {symbol}: Insufficient cash (need ${collateral_needed:,.2f}, have ${portfolio.available_cash:,.2f})")
                continue
            
            success = portfolio.add_order(
                symbol=symbol,
                quantity=args['quantity'],
                price=args.get('entry_price', 0),
                leverage=args['leverage'],
                profit_target=args['profit_target'],
                stop_loss=args['stop_loss'],
                confidence=args['confidence']
            )
            
            if success:
                print(f"✅ {symbol}: Order added successfully (Qty: {args['quantity']}, Price: ${args.get('entry_price', 0):.2f})")
            else:
                print(f"⚠️  {symbol}: Order not added (position may already exist)")
    else:
        print("\nNo new trading signals generated.")
    print("\n" + "="*80)

    # Save portfolio after all updates
    portfolio.save_to_file(PORTFOLIO_FILE)
    
    # Display portfolio metrics
    total_pnl = portfolio.total_pnl()
    print(f"\n💰 Portfolio Metrics:")
    print(f"  Available Cash: ${portfolio.available_cash:,.2f}")
    print(f"  Total Asset Value: ${portfolio.total_asset:,.2f}")
    print(f"  Total Unrealized PnL: ${total_pnl:,.2f}")
    
    # Sleep to prevent excessive API calls
    time.sleep(1)  # Wait 60 seconds before next loop
