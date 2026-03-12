"""
Trading strategy implementation - EMA Crossover with RSI and ATR filters
"""
import pandas as pd
from typing import Optional, Literal
from config import Config


class Strategy:
    """EMA Crossover strategy with RSI and ATR filters"""

    # Columns that must be present and non-NaN before any signal evaluation
    _REQUIRED_INDICATOR_COLS = ['ema_fast', 'ema_slow', 'rsi', 'atr', 'atr_mean']
    
    def __init__(self, config: Config):
        """Initialize strategy
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Strategy parameters
        self.ema_fast_period = config.get('strategy.ema_fast_period', 20)
        self.ema_slow_period = config.get('strategy.ema_slow_period', 50)
        self.rsi_period = config.get('strategy.rsi_period', 14)
        self.rsi_min = config.get('strategy.rsi_min', 40)
        self.rsi_max = config.get('strategy.rsi_max', 60)
        self.atr_period = config.get('strategy.atr_period', 14)
        self.atr_volatility_threshold = config.get('strategy.atr_volatility_threshold', 0.8)
        
    def _indicators_valid(self, df: pd.DataFrame) -> bool:
        """Check that the two most recent rows have valid (non-NaN) indicator values.

        All columns in ``_REQUIRED_INDICATOR_COLS`` are validated for the current
        (most recent) row.  Only ``ema_fast`` and ``ema_slow`` are validated for the
        previous row because those are the only values read from it (for crossover
        detection); the other indicators are only consumed from the current row.

        Returns:
            True if all required indicators are present and non-NaN, False otherwise
        """
        if len(df) < 2:
            return False
        current = df.iloc[-1]
        previous = df.iloc[-2]
        # Validate all required columns for the current bar
        if any(pd.isna(current[col]) for col in self._REQUIRED_INDICATOR_COLS):
            return False
        # For the previous bar only the EMA values are used (crossover check)
        if pd.isna(previous['ema_fast']) or pd.isna(previous['ema_slow']):
            return False
        return True

    def should_open_long(self, df: pd.DataFrame, spread_points: float) -> bool:
        """Check if conditions are met to open a long position
        
        Args:
            df: DataFrame with OHLC data and indicators
            spread_points: Current spread in points
            
        Returns:
            True if should open long, False otherwise
        """
        if not self._indicators_valid(df):
            return False
        
        # Get current and previous candles
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for bullish EMA crossover
        cross_up = (previous['ema_fast'] <= previous['ema_slow'] and 
                   current['ema_fast'] > current['ema_slow'])
        
        # Check RSI is in acceptable range (not overbought/oversold)
        rsi_ok = self.rsi_min < current['rsi'] < self.rsi_max
        
        # Check ATR is above threshold (sufficient volatility)
        vol_ok = current['atr'] > current['atr_mean'] * self.atr_volatility_threshold
        
        # Check spread is acceptable
        spread_ok = spread_points <= self.config.max_spread_points
        
        return cross_up and rsi_ok and vol_ok and spread_ok
    
    def should_open_short(self, df: pd.DataFrame, spread_points: float) -> bool:
        """Check if conditions are met to open a short position
        
        Args:
            df: DataFrame with OHLC data and indicators
            spread_points: Current spread in points
            
        Returns:
            True if should open short, False otherwise
        """
        if not self._indicators_valid(df):
            return False
        
        # Get current and previous candles
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for bearish EMA crossover
        cross_down = (previous['ema_fast'] >= previous['ema_slow'] and 
                     current['ema_fast'] < current['ema_slow'])
        
        # Check RSI is in acceptable range
        rsi_ok = self.rsi_min < current['rsi'] < self.rsi_max
        
        # Check ATR is above threshold
        vol_ok = current['atr'] > current['atr_mean'] * self.atr_volatility_threshold
        
        # Check spread is acceptable
        spread_ok = spread_points <= self.config.max_spread_points
        
        return cross_down and rsi_ok and vol_ok and spread_ok
    
    def should_close_position(self, df: pd.DataFrame, position_type: Literal['long', 'short']) -> bool:
        """Check if should close current position based on opposite crossover
        
        Args:
            df: DataFrame with OHLC data and indicators
            position_type: 'long' or 'short'
            
        Returns:
            True if should close position, False otherwise
        """
        if len(df) < 2:
            return False
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        if position_type == 'long':
            # Close long on bearish crossover
            return (previous['ema_fast'] >= previous['ema_slow'] and 
                   current['ema_fast'] < current['ema_slow'])
        else:
            # Close short on bullish crossover
            return (previous['ema_fast'] <= previous['ema_slow'] and 
                   current['ema_fast'] > current['ema_slow'])
    
    def get_signal(self, df: pd.DataFrame, spread_points: float) -> Optional[Literal['long', 'short']]:
        """Get trading signal
        
        Args:
            df: DataFrame with OHLC data and indicators
            spread_points: Current spread in points
            
        Returns:
            'long', 'short', or None
        """
        if self.should_open_long(df, spread_points):
            return 'long'
        elif self.should_open_short(df, spread_points):
            return 'short'
        return None
