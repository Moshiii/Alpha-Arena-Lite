"""
Hyperliquid market data service using CCXT
"""
import ccxt
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import time
import pandas as pd
import json
from stockstats import StockDataFrame

logger = logging.getLogger(__name__)

class HyperliquidClient:
    def __init__(self):
        self.exchange = None
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize CCXT Hyperliquid exchange"""
        try:
            self.exchange = ccxt.hyperliquid({
                'sandbox': False,  # Set to True for testnet
                'enableRateLimit': True,
            })
            logger.info("Hyperliquid exchange initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Hyperliquid exchange: {e}")
            raise

    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the last price for a symbol"""
        try:
            if not self.exchange:
                self._initialize_exchange()
            
            # Ensure symbol is in CCXT format (e.g., 'BTC/USD')
            formatted_symbol = self._format_symbol(symbol)
            
            ticker = self.exchange.fetch_ticker(formatted_symbol)
            price = ticker['last']
            
            logger.info(f"Got price for {formatted_symbol}: {price}")
            return float(price) if price else None
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    def get_kline_data(self, symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data for a symbol"""
        try:
            if not self.exchange:
                self._initialize_exchange()
            
            formatted_symbol = self._format_symbol(symbol)
            
            # Map period to CCXT timeframe
            timeframe_map = {
                '1m': '1m',
                '3m': '3m',
                '5m': '5m', 
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '4h': '4h',
                '1d': '1d',
            }
            timeframe = timeframe_map.get(period, '1d')
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=count)
            
            # Convert to our format
            klines = []
            for candle in ohlcv:
                timestamp_ms = candle[0]
                open_price = candle[1]
                high_price = candle[2]
                low_price = candle[3]
                close_price = candle[4]
                volume = candle[5]
                
                # Calculate change
                change = close_price - open_price if open_price else 0
                percent = (change / open_price * 100) if open_price else 0
                
                klines.append({
                    'timestamp': int(timestamp_ms / 1000),  # Convert to seconds
                    'datetime_str': datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat(),
                    'open': float(open_price) if open_price else None,
                    'high': float(high_price) if high_price else None,
                    'low': float(low_price) if low_price else None,
                    'close': float(close_price) if close_price else None,
                    'volume': float(volume) if volume else None,
                    'amount': float(volume * close_price) if volume and close_price else None,
                    'change': float(change),
                    'percent': float(percent),
                })
            
            logger.info(f"Got {len(klines)} klines for {formatted_symbol}")
            return klines
            
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return []

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for CCXT (e.g., 'BTC' -> 'BTC/USDC:USDC')"""
        if '/' in symbol and ':' in symbol:
            return symbol
        elif '/' in symbol:
            # If it's BTC/USDC, convert to BTC/USDC:USDC for Hyperliquid
            return f"{symbol}:USDC"
        
        # For single symbols like 'BTC', check if it's a mainstream crypto
        symbol_upper = symbol.upper()
        mainstream_cryptos = ['BTC', 'ETH', 'SOL', 'DOGE', 'BNB', 'XRP']
        
        if symbol_upper in mainstream_cryptos:
            # Use perpetual swap format for mainstream cryptos
            return f"{symbol_upper}/USDC:USDC"
        else:
            # Use spot format for other cryptos
            return f"{symbol_upper}/USDC"


def symbol_data_provider_json(symbol: str, frequency: str, count: int) -> Dict[str, Any]:
    """Get comprehensive market data for a symbol"""
    client = HyperliquidClient()
    
    period_map = {'1m': '1m', '3m': '3m', '5m': '5m', '1h': '1h', '4h': '4h', '1d': '1d'}
    timeframe = period_map.get(frequency, frequency)
    
    klines = client.get_kline_data(symbol, period=timeframe, count=count)
    print(f"Got {len(klines)} klines for {symbol} {frequency} {count}")
    if not klines:
        return {}
    
    df = pd.DataFrame(klines)
    df['datetime'] = pd.to_datetime(df['datetime_str'])
    df = df.set_index('datetime')
    
    stock = StockDataFrame.retype(df[['open', 'high', 'low', 'close', 'volume']])
    
    stock['rsi_7']
    stock['rsi_14']
    stock['macd']
    stock['macds']
    stock['close_20_ema']
    stock['atr_3']
    stock['atr_14']
    stock['close_50_ema']
    
    latest = stock.tail(1)
    past_10 = stock.tail(count)
    
    mid_prices = ((past_10['high'] + past_10['low']) / 2).tolist()
    
    result = {
        'current_price': float(latest['close'].iloc[0]),
        'current_close_20_ema': float(latest['close_20_ema'].iloc[0]),
        'current_macd': float(latest['macd'].iloc[0]),
        'current_rsi_7': float(latest['rsi_7'].iloc[0]),
        'current_volume': float(latest['volume'].iloc[0]),
        'average_volume': float(past_10['volume'].mean()),
        'open_interest_latest': float(latest['volume'].iloc[0]),
        'open_interest_average': float(past_10['volume'].mean()),
        'funding_rate': 0.0,
        'mid_prices': mid_prices,
        'ema_close_20_array': past_10['close_20_ema'].tolist(),
        'macd_array': past_10['macd'].tolist(),
        'rsi_7_array': past_10['rsi_7'].tolist(),
        'rsi_14_array': past_10['rsi_14'].tolist(),
        'ema_20_array': past_10['close_20_ema'].tolist(),
        'ema_50_array': past_10['close_50_ema'].tolist(),
        'atr_3_array': past_10['atr_3'].tolist(),
        'atr_14_array': past_10['atr_14'].tolist()
    }
    
    return result

# Global client instance
hyperliquid_client = HyperliquidClient()


def get_last_price_from_hyperliquid(symbol: str) -> Optional[float]:
    """Get last price from Hyperliquid"""
    return hyperliquid_client.get_last_price(symbol)
