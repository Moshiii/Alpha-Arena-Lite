"""
Trading Decision Provider - Generates trading signals based on market data
"""
from typing import Dict, Any
import random


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
    
    for symbol, market_data in market_data_dict.items():
        
        current_price = market_data.get('current_price', 0)
        
        direction = random.choice([-1, 0, 1, 2])
        signal = "buy" if direction == 1 else "hold" if direction == 0 else "sell" if direction == -1 else "close"
        quantity = random.uniform(0.00001, 0.01)
        leverage = random.choice([1, 5, 10, 15, 20, 25])
        confidence = random.uniform(0.5, 1.0)
        risk_per_trade = random.uniform(100, 1000)
        profit_target = random.uniform(current_price * 1.1, current_price * 1.2)
        stop_loss = random.uniform(current_price * 0.9, current_price * 0.95)
        invalidation_condition = random.choice(["If the price closes below {stop_loss:.2f} on a 3-minute candle", "If the price closes above {profit_target:.2f} on a 3-minute candle"])
        
        all_decisions[symbol] = {
            "trade_signal_args": {
                "coin": symbol,
                "signal": signal,
                "quantity": round(abs(quantity) * direction, 4),
                "profit_target": round(profit_target, 2),
                "stop_loss": round(stop_loss, 2),
                "invalidation_condition": invalidation_condition,
                "leverage": leverage,
                "confidence": round(confidence, 2),
                "risk_usd": risk_per_trade,
                "entry_price": round(current_price, 2)
            }
        }
    
    return all_decisions

