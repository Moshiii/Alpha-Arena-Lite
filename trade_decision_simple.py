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
    
    # Get existing positions from portfolio
    existing_positions = {pos['symbol']: pos for pos in portfolio_json.get('positions', [])}
    
    for symbol, market_data in market_data_dict.items():
        # Skip if position already exists and has quantity
        existing_pos = existing_positions.get(symbol)
        if existing_pos and existing_pos.get('quantity', 0) != 0:
            continue
        
        current_price = market_data.get('current_price', 0)
        rsi_7 = market_data.get('current_rsi_7', 50)
        macd = market_data.get('current_macd', 0)
        atr_3 = market_data.get('atr_3_array', [0])[-1] if market_data.get('atr_3_array') else 0
        atr_14 = market_data.get('atr_14_array', [0])[-1] if market_data.get('atr_14_array') else 0
        
        # Determine signal based on technical indicators
        signal = "hold"
        
        # Buy signal: RSI oversold AND MACD bullish
        if rsi_7 < 35 and macd > 0:
            signal = "buy"
        # Sell signal: RSI overbought
        elif rsi_7 > 70:
            signal = "sell"
        
        # Only generate decision for active signals
        if signal == "hold":
            continue
        
        # Calculate ATR-based stop loss and profit targets
        atr_avg = (atr_3 + atr_14) / 2 if atr_3 > 0 and atr_14 > 0 else current_price * 0.02
        
        # For buy signals: set profit target and stop loss
        if signal == "buy":
            profit_target = current_price + (atr_avg * 2.5)
            stop_loss = current_price - (atr_avg * 1.5)
            invalidation_price = current_price - (atr_avg * 3)
            invalidation_condition = f"If the price closes below {invalidation_price:.2f} on a 3-minute candle"
        else:  # sell
            profit_target = current_price - (atr_avg * 2.5)
            stop_loss = current_price + (atr_avg * 1.5)
            invalidation_price = current_price + (atr_avg * 3)
            invalidation_condition = f"If the price closes above {invalidation_price:.2f} on a 3-minute candle"
        
        # Calculate leverage based on volatility
        volatility = (atr_avg / current_price) if current_price > 0 else 0
        if volatility < 0.01:
            leverage = 15
        elif volatility < 0.02:
            leverage = 10
        else:
            leverage = 5
        
        # Calculate confidence
        if rsi_7 < 30 or rsi_7 > 70:
            confidence = 0.85
        elif rsi_7 < 40 or rsi_7 > 60:
            confidence = 0.70
        else:
            confidence = 0.60
        
        # Calculate position size and risk
        risk_per_trade = 500
        price_diff = abs(current_price - stop_loss)
        quantity = risk_per_trade / price_diff if price_diff > 0 else 0
        
        # Determine buy direction based on signal
        direction = 1 if signal == "buy" else -1
        
        direction = random.choice([-1, 1])
        signal = "buy" if direction == 1 else "sell"
        quantity = random.uniform(0.00001, 0.01)
        leverage = random.uniform(1, 10)
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

