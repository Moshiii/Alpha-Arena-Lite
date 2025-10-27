# Alpha-Arena-Lite

A cryptocurrency trading simulation platform that uses live market data from Hyperliquid and AI-powered trading decisions to manage a leveraged portfolio.

## Overview

Alpha-Arena-Lite is a trading simulation system that:
- Fetches real-time market data from Hyperliquid exchange
- Makes AI-powered trading decisions
- Manages a portfolio with leverage, profit targets, and stop losses
- Tracks positions, PnL, and portfolio performance

## Features

- **Live Market Data**: Fetches real-time prices and technical indicators from Hyperliquid
- **AI Trading Decisions**: Uses GPT-4o to generate trading signals based on market data and portfolio status
- **Portfolio Management**: Tracks positions with leverage, unrealized PnL, profit targets, and stop losses
- **Risk Management**: Built-in risk calculations and position sizing
- **Multiple Symbols**: Track and trade BTC, ETH, SOL, and more

## Requirements

- Python 3.8+
- OpenAI API key (for AI trading decisions)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Alpha-Arena-Lite.git
cd Alpha-Arena-Lite
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `ccxt` - Cryptocurrency exchange trading library
- `pandas` - Data manipulation and analysis
- `stockstats` - Technical indicators (RSI, MACD, EMA, ATR)
- `openai` - OpenAI API for AI-powered trading decisions

3. Set up environment variables:
```bash
# Create a .env file or export the API key
export OPENAI_API_KEY="your-api-key-here"
```

## Configuration

### 1. Portfolio Initialization

The simulation starts by loading a portfolio from `portfolio_init.json`. This file defines:
- Initial starting capital
- Initial positions (if any)
- Available cash

Example `portfolio_init.json`:
```json
{
  "positions": [
    {
      "symbol": "BTC",
      "quantity": 0.0,
      "entry_price": 0.0,
      "current_price": 0.0,
      "liquidation_price": null,
      "leverage": 1.0,
      "unrealized_pnl": 0.0,
      "entry_time": "2025-01-01T00:00:00.000000"
    },
    {
      "symbol": "ETH",
      "quantity": 0.0,
      "entry_price": 0.0,
      "current_price": 0.0,
      "liquidation_price": null,
      "leverage": 1.0,
      "unrealized_pnl": 0.0,
      "entry_time": "2025-01-01T00:00:00.000000"
    },
    {
      "symbol": "SOL",
      "quantity": 0.0,
      "entry_price": 0.0,
      "current_price": 0.0,
      "liquidation_price": null,
      "leverage": 1.0,
      "unrealized_pnl": 0.0,
      "entry_time": "2025-01-01T00:00:00.000000"
    }
  ],
  "timestamp": "2025-01-01T00:00:00.000000",
  "initial_cash": 1000000.0,
  "available_cash": 1000000.0,
  "total_asset": 1000000.0
}
```

### 2. Simulation Configuration

Edit `simulation.py` to configure:
- **SYMBOLS**: List of cryptocurrencies to track (default: `['BTC', 'ETH', 'SOL']`)
- **PORTFOLIO_FILE**: File to save portfolio state (default: `'portfolio.json'`)
- **BUY_QUANTITY**: Fixed buy quantity per loop (default: `0.0001`)
- **Loop interval**: Sleep time between updates (default: `1 second`)

Example configuration:
```python
SYMBOLS = ['BTC', 'ETH', 'SOL']
PORTFOLIO_FILE = 'portfolio.json'
BUY_QUANTITY = 0.0001
```

## Running the Simulation

### Basic Usage

1. Start the simulation:
```bash
python simulation.py
```

2. The simulation will:
   - Load the portfolio from `portfolio_init.json`
   - Fetch market data for configured symbols
   - Generate AI trading decisions
   - Execute trades based on decisions
   - Update portfolio with live prices
   - Save portfolio state to `portfolio.json`

### Example Output

```
Loaded existing portfolio
Initial Cash: $1,000,000.00
Available Cash: $1,000,000.00

14:23:45 - Loop #1 - Fetching market data...
[Market data for BTC]
BTC: $45,250.00
[Market data for ETH]
ETH: $3,125.00

📊 Portfolio Status:
Current Total Return (percent): 0.00%
Available Cash: $1,000,000.00
Current Account Value: $1,000,000.00

📊 Generating Trading Decisions...

BTC Trading Decision:
  Signal: buy
  Quantity: 0.5
  Entry Price: $45,250.00
  Profit Target: $48,000.00
  Stop Loss: $43,000.00
  Leverage: 10x
  Confidence: 0.75
  Risk: $1,125.00
```

## File Structure

```
Alpha-Arena-Lite/
├── simulation.py              # Main simulation loop
├── simple_portfolio.py        # Portfolio management class
├── hyperliquid_market_data.py # Market data fetching
├── trade_decision_simple_AI.py  # AI trading decisions
├── trade_decision_simple.py   # Rule-based trading decisions
├── simple_usage.py            # Basic usage example
├── requirements.txt           # Python dependencies
├── portfolio_init.json        # Initial portfolio configuration
├── portfolio.json            # Current portfolio state (generated)
└── test/
    └── test_simple_portfolio.py  # Unit tests
```

## Key Components

### SimplePortfolio
Manages portfolio state including:
- Positions tracking (one per symbol)
- Available cash
- Unrealized PnL calculation
- Leverage support
- JSON persistence

### Hyperliquid Market Data
Fetches:
- Real-time prices
- OHLCV candlestick data
- Technical indicators (RSI, MACD, EMA, ATR)
- Volume and open interest

### AI Trading Decisions
Uses GPT-4o to analyze:
- Current market conditions
- Technical indicators
- Portfolio status
- Risk parameters

Generates trading signals with:
- Entry price, quantity
- Profit targets and stop losses
- Leverage recommendations
- Confidence scores
- Risk calculations

## Configuration Options

### Changing Symbols to Track
Edit `simulation.py`:
```python
SYMBOLS = ['BTC', 'ETH', 'SOL', 'DOGE', 'BNB']  # Add more symbols
```

### Adjusting Loop Interval
Edit `simulation.py`:
```python
time.sleep(60)  # Wait 60 seconds before next loop
```

### Using Different Trading Decision Providers
Edit `simulation.py`:
```python
from trade_decision_simple import trade_decision_provider  # Rule-based
# OR
from trade_decision_simple_AI import trade_decision_provider  # AI-based
```

## Portfolio Management

### Position Structure
Each position contains:
- Symbol (e.g., 'BTC')
- Quantity (positive for long, negative for short)
- Entry price
- Current price
- Liquidation price (calculated based on leverage)
- Leverage multiplier
- Unrealized PnL

### Risk Management
- Collateral calculation based on leverage
- Stop loss enforcement
- Profit target tracking
- Maximum risk per trade

## Troubleshooting

### Missing agents Module
If you encounter `ModuleNotFoundError: No module named 'agents'`, you need to:
1. Check if the Agent class exists in your environment
2. Create an `agents.py` file with the Agent class implementation
3. Or install the required agent framework

### API Rate Limiting
Hyperliquid API has rate limits. Adjust the sleep time in `simulation.py` to avoid rate limiting:
```python
time.sleep(10)  # Increase wait time
```

### Insufficient Cash
If trades fail with "Insufficient cash" error:
- Adjust the initial cash in `portfolio_init.json`
- Or reduce trade quantities in your trading decision logic

## Testing

Run the test suite:
```bash
python -m pytest test/
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues and questions, please open an issue on the GitHub repository.
