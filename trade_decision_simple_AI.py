"""
Trading Decision Provider - Generates trading signals based on market data
"""
from typing import Dict, Any
from hyperliquid_market_data import to_string
from agents import Agent
import json

def portfolio_to_string(portfolio_json: Dict[str, Any]) -> str:
    """Convert portfolio JSON to formatted string"""
    result_string = "HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE\n"
    
    # Calculate total return
    initial_cash = portfolio_json.get('initial_cash', 10000.0)
    total_asset = portfolio_json.get('total_asset', 0)
    total_return = ((total_asset - initial_cash) / initial_cash) * 100 if initial_cash > 0 else 0
    
    result_string += f"Current Total Return (percent): {total_return:.2f}%\n"
    result_string += f"Available Cash: {portfolio_json.get('available_cash', 0):.2f}\n"
    result_string += f"Current Account Value: {total_asset:.2f}\n"
    result_string += "Current live positions & performance:\n\n"
    
    # Display each position
    positions = portfolio_json.get('positions', [])
    for pos in positions:
        result_string += f"Symbol: {pos.get('symbol', 'N/A')}, "
        result_string += f"Qty: {pos.get('quantity', 0):.4f}, "
        result_string += f"Entry: ${pos.get('entry_price', 0):.2f}, "
        result_string += f"Current: ${pos.get('current_price', 0):.2f}, "
        result_string += f"PnL: ${pos.get('unrealized_pnl', 0):.2f}, "
        result_string += f"Leverage: {pos.get('leverage', 1)}x\n"
    
    return result_string

def trade_decision_provider(market_data_dict: Dict[str, Dict[str, Any]], portfolio_json: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Generate trading decisions for all symbols based on market data and portfolio
    
    Args:
        market_data_dict: Dictionary of market data for each symbol from symbol_data_provider_json
        portfolio_json: Portfolio JSON data from SimplePortfolio.return_json()
    
    Returns:
        Dictionary with trading decisions for each symbol
    """
    all_decisions = {}
    
    # Get existing positions from portfolio
    
    market_data_string = to_string(market_data_dict)
    portfolio_json_string = portfolio_to_string(portfolio_json)
    MARKET_PROMPT = f"""
    You are a trading agent. You are given the following market data:
    {market_data_string}
    You are also given the following portfolio information:
    {portfolio_json_string}
    You need to generate a trading decision for the following symbol:
    {market_data_dict.keys()}
    The trading decision should be a JSON object with the following fields, for example:
    The trading decision should be formatted as a JSON array where each element is an object describing the trading signal for a single symbol. The required fields for each object are:

    - "coin": (string) The ticker symbol of the asset (e.g. "BTC", "ETH", "SOL")
    - "signal": (string) One of "buy", "sell", or "hold"
    - "quantity": (number) The amount of the asset to trade (can be positive or negative for buy/sell)
    - "profit_target": (number) The price at which to take profit
    - "stop_loss": (number) The price at which to cut losses
    - "invalidation_condition": (string) A description of the price/action/reason the trade would be considered invalid, e.g. "If the price closes below 3800 on a 3-minute candle"
    - "leverage": (number) The leverage to use for the trade
    - "confidence": (number) A value between 0 and 1 indicating your confidence level in the signal
    - "risk_usd": (number) The dollar amount the strategy is willing to risk on this trade

    Example format:
    [
      {
        "coin": "ETH",
        "signal": "hold",
        "quantity": 4.87,
        "profit_target": 4227.35,
        "stop_loss": 3714.95,
        "invalidation_condition": "If the price closes below 3800 on a 3-minute candle",
        "leverage": 15,
        "confidence": 0.75,
        "risk_usd": 624.38
      },
      {
        "coin": "SOL",
        "signal": "hold",
        "quantity": 81.81,
        "profit_target": 201.081,
        "stop_loss": 176.713,
        "invalidation_condition": "If the price closes below 175 on a 3-minute candle",
        "leverage": 15,
        "confidence": 0.75,
        "risk_usd": 499.504
      },
      {
        "coin": "BTC",
        "signal": "hold",
        "quantity": 0.12,
        "profit_target": 118136.15,
        "stop_loss": 102026.675,
        "invalidation_condition": "If the price closes below 105000 on a 3-minute candle",
        "leverage": 10,
        "confidence": 0.75,
        "risk_usd": 619.2345
      }
    ]
    """
    
    market_agent = Agent(
        name="SimpleTradeDecisionAgent",
        instructions=MARKET_PROMPT,
        model="gpt-4o",
    ) 
    
    response = market_agent.run(MARKET_PROMPT)
    all_decisions = json.loads(response)
    
    
    return all_decisions

