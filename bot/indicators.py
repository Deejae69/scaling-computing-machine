"""
Technical indicators calculation using ta library
"""
import pandas as pd
import ta


class Indicators:
    """Calculate technical indicators for trading strategy"""
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average
        
        Args:
            df: DataFrame with price data
            period: EMA period
            column: Column name to calculate EMA on
            
        Returns:
            Series with EMA values
        """
        return ta.trend.ema_indicator(df[column], window=period)
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
        """Calculate Relative Strength Index
        
        Args:
            df: DataFrame with price data
            period: RSI period
            column: Column name to calculate RSI on
            
        Returns:
            Series with RSI values
        """
        return ta.momentum.rsi(df[column], window=period)
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            Series with ATR values
        """
        return ta.volatility.average_true_range(
            df['high'], 
            df['low'], 
            df['close'], 
            window=period
        )
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame, 
                          ema_fast: int = 20,
                          ema_slow: int = 50,
                          rsi_period: int = 14,
                          atr_period: int = 14) -> pd.DataFrame:
        """Add all required indicators to DataFrame
        
        Args:
            df: DataFrame with OHLC data
            ema_fast: Fast EMA period
            ema_slow: Slow EMA period
            rsi_period: RSI period
            atr_period: ATR period
            
        Returns:
            DataFrame with all indicators added
        """
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Add indicators
        df['ema_fast'] = Indicators.calculate_ema(df, ema_fast)
        df['ema_slow'] = Indicators.calculate_ema(df, ema_slow)
        df['rsi'] = Indicators.calculate_rsi(df, rsi_period)
        df['atr'] = Indicators.calculate_atr(df, atr_period)
        
        # Add ATR rolling mean for volatility filter
        df['atr_mean'] = df['atr'].rolling(window=100).mean()
        
        return df
