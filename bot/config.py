"""
Configuration loader for MT5 Trading Bot
"""
import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Configuration manager for the trading bot"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration
        
        Args:
            config_path: Path to YAML configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load YAML config with error handling
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.") from e
        except OSError as e:
            raise OSError(f"Could not open configuration file '{config_path}': {e}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML configuration file '{config_path}': {e}") from e
        
        # MT5 Credentials from environment
        try:
            self.mt5_login = int(os.getenv('MT5_LOGIN', '0'))
        except ValueError:
            self.mt5_login = 0
        self.mt5_password = os.getenv('MT5_PASSWORD', '')
        self.mt5_server = os.getenv('MT5_SERVER', '')
        
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path (e.g., 'risk.equity_risk_percent')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    @property
    def symbol(self) -> str:
        return self.get('trading.symbol', 'EURUSD')
    
    @property
    def timeframe_str(self) -> str:
        return self.get('trading.timeframe', 'M5')
    
    @property
    def max_spread_points(self) -> int:
        return self.get('trading.max_spread_points', 15)
    
    @property
    def equity_risk_percent(self) -> float:
        return self.get('risk.equity_risk_percent', 1.0)
    
    @property
    def daily_loss_cap_percent(self) -> float:
        return self.get('risk.daily_loss_cap_percent', 2.5)
    
    @property
    def max_consecutive_losses(self) -> int:
        return self.get('risk.max_consecutive_losses', 3)
    
    @property
    def atr_stop_multiplier(self) -> float:
        return self.get('risk.atr_stop_multiplier', 1.8)
    
    @property
    def risk_reward_ratio(self) -> float:
        return self.get('risk.risk_reward_ratio', 1.7)
    
    @property
    def enable_trailing_stop(self) -> bool:
        return self.get('risk.enable_trailing_stop', True)
    
    @property
    def magic_number(self) -> int:
        return self.get('execution.magic_number', 12345)
    
    @property
    def lookback_bars(self) -> int:
        return self.get('data.lookback_bars', 500)
    
    @property
    def is_backtest_mode(self) -> bool:
        return self.get('mode.backtest', False)
    
    @property
    def is_paper_trade_mode(self) -> bool:
        return self.get('mode.paper_trade', True)
    
    @property
    def is_live_trade_mode(self) -> bool:
        return self.get('mode.live_trade', False)
