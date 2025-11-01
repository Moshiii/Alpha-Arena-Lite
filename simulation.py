"""
Simple Market Data Simulation - Buy positions and update portfolio every loop
"""
import time
import signal
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from hyperliquid_market_data import symbol_data_provider_json
from simple_portfolio import SimplePortfolio
from trade_decision_simple_AI import trade_decision_provider

# Configuration constants
SYMBOLS = ['BTC', 'ETH', 'SOL']
PORTFOLIO_FILE = 'portfolio.json'
PORTFOLIO_INIT_FILE = 'portfolio_init.json'
UPDATE_FREQUENCY = '3m'
KLINE_COUNT = 10
LOOP_SLEEP_SECONDS = 1  # Sleep duration between loops in seconds
DISPLAY_INTERVAL = 1  # Display portfolio every N loops (1 = every loop)

# Load environment variables
load_dotenv()

# Global shutdown flag for graceful shutdown
shutdown = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global shutdown
    print("\n\n⚠️  Shutdown signal received. Finishing current loop...")
    shutdown = True


def safe_fetch_market_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Safely fetch market data for a symbol with error handling"""
    try:
        json_result = symbol_data_provider_json(symbol, UPDATE_FREQUENCY, KLINE_COUNT)
        if not json_result or 'current_price' not in json_result:
            print(f"⚠️  {symbol}: No valid kline data returned")
            return None
        return json_result
    except Exception as e:
        print(f"❌ {symbol}: Error fetching market data: {e}")
        return None


# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Load or create portfolio
portfolio = SimplePortfolio()

try:
    portfolio.load_from_file(PORTFOLIO_INIT_FILE)
    print("✅ Loaded existing portfolio")
    print(f"Initial Cash: ${portfolio.initial_cash:,.2f}")
    print(f"Available Cash: ${portfolio.available_cash:,.2f}")
    portfolio.display()
except FileNotFoundError:
    print("📝 Creating new portfolio")
    print(f"Initial Cash: ${portfolio.initial_cash:,.2f}")
except Exception as e:
    print(f"❌ Error loading portfolio: {e}")
    print("📝 Starting with new portfolio")

loop_count = 0
portfolio_changed = False

print("\n🚀 Starting simulation loop. Press Ctrl+C to stop gracefully.\n")

while not shutdown:
    try:
        loop_count += 1
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Loop #{loop_count} - Fetching market data...")
        
        market_data_for_decisions_json = {}
        successful_fetches = 0
        
        # Fetch market data for each symbol
        for symbol in SYMBOLS:
            json_result = safe_fetch_market_data(symbol)
            if json_result is None:
                continue
            
            # Add symbol and frequency to json_result
            json_result['symbol'] = symbol
            json_result['frequency'] = UPDATE_FREQUENCY
            
            current_price = json_result['current_price']
            print(f"✅ {symbol}: ${current_price:,.2f}")
            
            # Update portfolio prices
            portfolio.update_price(symbol, current_price)
            portfolio.update_unrealized_pnl(symbol)
            market_data_for_decisions_json[symbol] = json_result
            successful_fetches += 1
        
        # Skip decision making if no market data was fetched
        if successful_fetches == 0:
            print("⚠️  No market data fetched for any symbol. Skipping this loop.")
            time.sleep(LOOP_SLEEP_SECONDS)
            continue
        
        # Display portfolio (at intervals or when changed)
        if loop_count % DISPLAY_INTERVAL == 0 or portfolio_changed:
            portfolio.display()
        
        portfolio_json = portfolio.return_json()
        
        # Generate trading decisions
        print("\n📊 Generating Trading Decisions...")
        
        try:
            all_decisions = trade_decision_provider(market_data_for_decisions_json, portfolio_json)
        except Exception as e:
            print(f"❌ Error generating trading decisions: {e}")
            all_decisions = {}
        
        if not all_decisions:
            print("\n⏸️  No new trading signals generated.")
        else:
            print(all_decisions)
            portfolio.decisions_display(all_decisions)
            
            print("\n📝 Executing Orders...")
            portfolio_changed = False
            
            for symbol, decision_data in all_decisions.items():
                if portfolio.execute_decision(symbol=symbol, decision_data=decision_data):
                    portfolio_changed = True
        
        print("\n" + "="*80)
        
        # Save portfolio only if it changed
        if portfolio_changed:
            try:
                portfolio.save_to_file(PORTFOLIO_FILE)
                print("💾 Portfolio saved to file")
            except Exception as e:
                print(f"❌ Error saving portfolio: {e}")
        
        # Display portfolio metrics
        total_pnl = portfolio.total_pnl()
        print(f"\n💰 Portfolio Metrics:")
        print(f"  Available Cash: ${portfolio.available_cash:,.2f}")
        print(f"  Total Asset Value: ${portfolio.total_asset:,.2f}")
        print(f"  Total Unrealized PnL: ${total_pnl:,.2f}")
        
        # Sleep to prevent excessive API calls
        time.sleep(LOOP_SLEEP_SECONDS)
        
    except KeyboardInterrupt:
        # This should be caught by signal handler, but just in case
        break
    except Exception as e:
        print(f"\n❌ Unexpected error in main loop: {e}")
        print("Continuing to next iteration...")
        time.sleep(LOOP_SLEEP_SECONDS)

# Final save on shutdown
print("\n\n🛑 Shutting down gracefully...")
try:
    portfolio.save_to_file(PORTFOLIO_FILE)
    print("✅ Portfolio saved before shutdown")
except Exception as e:
    print(f"❌ Error saving portfolio on shutdown: {e}")

print("👋 Simulation stopped.")
