"""
Trading Decision Provider - Generates trading signals based on market data
"""
from typing import Dict, Any, List

import json
import math
import os
import dotenv
dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def _fmt_number(value: Any, decimals: int = 2) -> str:
    try:
        if value is None:
            return "N/A"
        if isinstance(value, float) and math.isnan(value):
            return "N/A"
        fmt = f"{value:.{decimals}f}"
        return fmt
    except Exception:
        return str(value)


def portfolio_to_string(portfolio_json: Dict[str, Any], symbol: str = None) -> str:
    """Convert portfolio JSON to a concise, human‑readable summary."""
    result_string = "HERE IS YOUR ACCOUNT INFORMATION & PERFORMANCE\n"

    timestamp = portfolio_json.get('timestamp')
    if timestamp:
        result_string += f"As of: {timestamp}\n"

    initial_cash = float(portfolio_json.get('initial_cash', 0) or 0)
    total_asset = float(portfolio_json.get('total_asset', 0) or 0)
    available_cash = float(portfolio_json.get('available_cash', 0) or 0)
    total_pnl = float(portfolio_json.get('total_pnl', 0) or 0)

    total_return_pct = (100.0 * (total_asset - initial_cash) / initial_cash) if initial_cash > 0 else 0.0

    result_string += f"Current Total Return (percent): {_fmt_number(total_return_pct, 2)}%\n"
    result_string += f"Available Cash: ${_fmt_number(available_cash, 2)}\n"
    result_string += f"Current Account Value: ${_fmt_number(total_asset, 2)}\n"
    result_string += f"Total Unrealized PnL: ${_fmt_number(total_pnl, 2)}\n"
    result_string += "Current live positions & performance:\n\n"

    positions = portfolio_json.get('positions', []) or []
    if not positions:
        result_string += "(No open positions)\n"
        return result_string

    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        qty = float(pos.get('quantity', 0) or 0)
        entry = float(pos.get('entry_price', 0) or 0)
        current = float(pos.get('current_price', 0) or 0)
        pnl = float(pos.get('unrealized_pnl', 0) or 0)
        lev = pos.get('leverage', 1)
        notional = float(pos.get('notional_usd', 0) or 0)
        risk_usd = float(pos.get('risk_usd', 0) or 0)
        confidence = pos.get('confidence', None)

        line = (
            f"Symbol: {symbol}, "
            f"Qty: {_fmt_number(qty, 4)}, "
            f"Entry: ${_fmt_number(entry, 2)}, "
            f"Current: ${_fmt_number(current, 2)}, "
            f"PnL: ${_fmt_number(pnl, 2)}, "
            f"Notional: ${_fmt_number(notional, 2)}, "
            f"Risk: ${_fmt_number(risk_usd, 2)}, "
            f"Leverage: {lev}x"
        )
        if confidence is not None:
            line += f", Confidence: {_fmt_number(float(confidence), 2)}"
        result_string += line + "\n"

    return result_string
  
  
def market_data_to_string_for_symbol(market_data: Dict[str, Any], symbol: str) -> str:
  """Format a single symbol's market data to a concise, readable string."""

  def _fmt_series(series, decimals=3):
    cleaned = []
    for v in series or []:
      if v is None:
        continue
      if isinstance(v, float) and math.isnan(v):
        continue
      cleaned.append(f"{v:.{decimals}f}")
    return ', '.join(cleaned)

  freq_map = {
      '1m': '1-minute',
      '3m': '3-minute',
      '5m': '5-minute',
      '15m': '15-minute',
      '30m': '30-minute',
      '1h': 'hourly',
      '4h': '4-hour',
      '1d': 'daily'
  }

  symbol_upper = str(symbol).upper()
  intraday = market_data or {}
  frequency = intraday.get('frequency', '3m')
  interval_desc = freq_map.get(frequency, frequency)

  price = intraday.get('current_price')
  ema20 = intraday.get('current_close_20_ema')
  macd = intraday.get('current_macd')
  rsi7 = intraday.get('current_rsi_7')
  oi_latest = intraday.get('open_interest_latest')
  oi_avg = intraday.get('open_interest_average')
  funding = intraday.get('funding_rate')

  mid_prices_str = _fmt_series(intraday.get('mid_prices'), 2)
  ema_20_str = _fmt_series(intraday.get('ema_20_array'), 3)
  macd_str = _fmt_series(intraday.get('macd_array'), 3)
  rsi_7_str = _fmt_series(intraday.get('rsi_7_array'), 3)
  rsi_14_str = _fmt_series(intraday.get('rsi_14_array'), 3)

  lines = [
    f"ALL {symbol_upper} DATA",
    f"current_price = {_fmt_number(price, 3)}, current_ema20 = {_fmt_number(ema20, 3)}, current_macd = {_fmt_number(macd, 3)}, current_rsi (7 period) = {_fmt_number(rsi7, 3)}",
    f"Open Interest: Latest: {_fmt_number(oi_latest, 2)}  Average: {_fmt_number(oi_avg, 2)}",
    f"Funding Rate: {_fmt_number(funding, 6)}",
    f"Intraday series ({interval_desc} intervals, oldest → latest):",
    f"{symbol_upper} mid prices: [{mid_prices_str}]",
    f"EMA indicators (20‑period): [{ema_20_str}]",
    f"MACD indicators: [{macd_str}]",
    f"RSI indicators (7‑Period): [{rsi_7_str}]",
    f"RSI indicators (14‑Period): [{rsi_14_str}]",
  ]

  return "\n".join(lines)

def trade_decision_provider(market_data_dict: Dict[str, Dict[str, Any]], portfolio_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate trading decisions for all symbols based on market data and portfolio
    
    Args:
        market_data_dict: Dictionary of market data for each symbol from symbol_data_provider_json
        portfolio_json: Portfolio JSON data from SimplePortfolio.return_json()
    
    Returns:
        List of decision objects, one per symbol
    """
    decisions = {}
    for symbol, market_data in (market_data_dict or {}).items():
        md_str = market_data_to_string_for_symbol(market_data, symbol)
        pf_str = portfolio_to_string(portfolio_json, symbol)

        MARKET_PROMPT = f'''
        You are a trading agent. Here is the market data for {symbol}:
        {md_str}
        Here is the current portfolio information:
        {pf_str}
        
        INSTRUCTIONS:
        now pleae generate a trading decision for the symbol {symbol}
        the quantity should be within 30% of the total available cash.
        Generate ONLY for symbol {symbol} a single JSON object in the following structure:
        {{
        "trade_signal_args": {{
        "coin": <string>,
        "signal": <"buy" | "sell" | "hold" | "close">,
        "quantity": <number>,
        "profit_target": <number>,
        "stop_loss": <number>,
        "invalidation_condition": <string>,
        "leverage": <number>,
        "confidence": <number: between 0 and 1>,
        "risk_usd": <number>,
        "entry_price": <number>
        }}
        If you have no trading signal, set "signal" to "hold" and all numeric fields sensibly, matching the example below.
        Respond ONLY with your answer json, no text or explanation.
        Here is an example:
        {{'trade_signal_args': {{'coin': 'BTC', 'signal': 'hold', 'quantity': 0.0, 'profit_target': 125324.72, 'stop_loss': 103010.63, 'invalidation_condition': 'If the price closes below {{stop_loss:.2f}} on a 3-minute candle', 'leverage': 10, 'confidence': 0.78, 'risk_usd': 782.6279043220959, 'entry_price': 109750.0}}}}\n"
        Do not output an array. Always output a dict for a single symbol as in the example above.
        '''

        from openai import OpenAI

        # Initialize client
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Create a chat completion that returns structured JSON
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": MARKET_PROMPT}],
            response_format={"type": "json_object"}  # Ensures valid JSON
        )

        # The model's JSON output is accessible as a Python dict
        result = json.loads(response.choices[0].message.content)
        decisions[symbol] = result

    return decisions

