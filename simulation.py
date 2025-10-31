"""
Simple Market Data Simulation - Buy positions and update portfolio every loop
"""
import time
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from hyperliquid_market_data import get_last_price_from_hyperliquid, symbol_data_provider_json
from simple_portfolio import SimplePortfolio
# from trade_decision_rule_based import trade_decision_provider
# from trade_decision_simple import trade_decision_provider
from trade_decision_simple_AI import trade_decision_provider
# 加载环境变量
load_dotenv()

# Track these symbols
SYMBOLS = ['BTC', 'ETH', 'SOL']
PORTFOLIO_FILE = 'portfolio.json'
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
    
    for symbol in SYMBOLS:
        price = get_last_price_from_hyperliquid(symbol)
        json_result = symbol_data_provider_json(symbol, '3m', 10)
        if not json_result or 'current_price' not in json_result:
            print(f"Skipping {symbol}: no kline data returned this loop")
            continue
        # Add symbol and frequency to json_result for to_string
        json_result['price'] = price
        json_result['symbol'] = symbol
        json_result['frequency'] = '3m'
        print(f"{symbol}: ${price:,.2f}")
        # Store market data for later use in trade decisions
        market_data_for_decisions_json[symbol] = json_result
    
    for symbol, data in market_data_for_decisions_json.items():
        portfolio.update_price(symbol, data['price'])
        portfolio.update_unrealized_pnl(symbol)
    # Update portfolio prices and display
    portfolio.display()
    portfolio_json = portfolio.return_json()
    
    # Generate trading decisions
    print("\n📊 Generating Trading Decisions...")
    # print(market_data_for_decisions_json)
    # print(portfolio_json)
    
    all_decisions = trade_decision_provider(market_data_for_decisions_json, portfolio_json)
    print(all_decisions)
    portfolio.decisions_display(all_decisions)
    # Print the trading decisions
    if not all_decisions:   
        print("\nNo new trading signals generated.")
    else:
        for symbol, decision_data in all_decisions.items():
            # Execute orders based on decisions
            print("\n📝 Executing Orders...")
            for symbol, decision_data in all_decisions.items():
                args = decision_data["trade_signal_args"]

                # Handle explicit close signal
                if args.get('signal') == 'close':
                    portfolio.remove_position(symbol)
                    print(f"🛑 {symbol}: Position closed by signal.")
                    continue

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
