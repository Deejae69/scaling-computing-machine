"""
Risk management module for position sizing and risk controls
"""
import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from config import Config


class RiskManager:
    """Manages risk controls and position sizing"""
    
    def __init__(self, config: Config):
        """Initialize risk manager
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Track losses
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        self.daily_start_equity = 0.0
        self.last_reset_date = datetime.now().date()
        self.order_errors = 0
        self.max_order_errors = 5
        
        # Trade statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
    def reset_daily_stats(self, current_equity: float):
        """Reset daily statistics
        
        Args:
            current_equity: Current account equity
        """
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_start_equity = current_equity
            self.last_reset_date = today
            self.logger.info(f"Daily stats reset. Starting equity: {current_equity}")
    
    def record_trade_result(self, pnl: float):
        """Record trade result and update statistics
        
        Args:
            pnl: Profit/loss of the trade
        """
        self.daily_pnl += pnl
        self.total_trades += 1
        
        if pnl < 0:
            self.consecutive_losses += 1
            self.losing_trades += 1
            self.total_loss += abs(pnl)
            self.logger.warning(f"Loss recorded: {pnl}. Consecutive losses: {self.consecutive_losses}")
        elif pnl > 0:
            self.consecutive_losses = 0
            self.winning_trades += 1
            self.total_profit += pnl
            self.logger.info(f"Profit recorded: {pnl}. Consecutive losses reset.")
        else:
            # Break-even trade: reset consecutive losses but don't count as win or loss
            self.consecutive_losses = 0
            self.logger.info(f"Break-even trade recorded (PnL: {pnl}). Consecutive losses reset.")
        
        # Log statistics
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            self.logger.info(f"Stats: {self.total_trades} trades, {win_rate:.1f}% win rate, "
                           f"Total P&L: {self.total_profit - self.total_loss:.2f}")
    
    def record_order_error(self):
        """Record an order execution error"""
        self.order_errors += 1
        self.logger.error(f"Order error recorded. Total errors: {self.order_errors}")
    
    def reset_order_errors(self):
        """Reset order error counter"""
        self.order_errors = 0
    
    def can_trade(self, current_equity: float) -> Tuple[bool, str]:
        """Check if trading is allowed based on risk controls
        
        Args:
            current_equity: Current account equity
            
        Returns:
            Tuple of (can_trade, reason)
        """
        # Reset daily stats if needed
        self.reset_daily_stats(current_equity)
        
        # Check consecutive losses
        if self.consecutive_losses >= self.config.max_consecutive_losses:
            return False, f"Max consecutive losses reached ({self.consecutive_losses})"
        
        # Check daily loss cap
        if self.daily_start_equity > 0:
            daily_loss_pct = (self.daily_pnl / self.daily_start_equity) * 100
            if daily_loss_pct <= -self.config.daily_loss_cap_percent:
                return False, f"Daily loss cap reached ({daily_loss_pct:.2f}%)"
        
        # Check order errors (kill switch)
        if self.order_errors >= self.max_order_errors:
            return False, f"Too many order errors ({self.order_errors})"
        
        return True, "OK"
    
    def calculate_position_size(self, 
                                equity: float,
                                atr_value: float,
                                point: float,
                                volume_min: float,
                                volume_max: float,
                                volume_step: float) -> float:
        """Calculate position size based on risk parameters
        
        Args:
            equity: Current account equity
            atr_value: Current ATR value
            point: Symbol point value
            volume_min: Minimum allowed volume
            volume_max: Maximum allowed volume
            volume_step: Volume step size
            
        Returns:
            Position size (volume) in lots
        """
        # Calculate risk amount (1% of equity)
        risk_amount = equity * (self.config.equity_risk_percent / 100)
        
        # Calculate stop loss in points
        sl_points = int(self.config.atr_stop_multiplier * atr_value / point)
        
        # Avoid division by zero
        if sl_points == 0 or point == 0:
            self.logger.warning("Invalid SL points or point value, using minimum volume")
            return volume_min
        
        # Calculate volume based on risk
        volume = risk_amount / (sl_points * point)
        
        # Apply volume constraints
        volume = max(volume_min, min(volume, volume_max))
        
        # Round to volume step if valid to avoid division by zero
        if volume_step <= 0:
            self.logger.warning(
                "Invalid volume_step (%s); skipping volume rounding and using constrained volume",
                volume_step,
            )
        else:
            volume = round(volume / volume_step) * volume_step
        
        self.logger.info(f"Position size calculated: {volume} lots "
                        f"(risk: {risk_amount}, SL points: {sl_points})")
        
        return volume
    
    def calculate_stop_loss(self, entry_price: float, atr_value: float, 
                           point: float, position_type: str) -> float:
        """Calculate stop loss price
        
        Args:
            entry_price: Entry price
            atr_value: Current ATR value
            point: Symbol point value
            position_type: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        sl_points = int(self.config.atr_stop_multiplier * atr_value / point)
        
        if position_type == 'long':
            return entry_price - sl_points * point
        else:
            return entry_price + sl_points * point
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float,
                             position_type: str) -> float:
        """Calculate take profit price based on risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            position_type: 'long' or 'short'
            
        Returns:
            Take profit price
        """
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * self.config.risk_reward_ratio
        
        if position_type == 'long':
            return entry_price + tp_distance
        else:
            return entry_price - tp_distance
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trading statistics
        
        Returns:
            Dictionary with trading statistics
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        avg_win = self.total_profit / self.winning_trades if self.winning_trades > 0 else 0.0
        avg_loss = self.total_loss / self.losing_trades if self.losing_trades > 0 else 0.0
        profit_factor = self.total_profit / self.total_loss if self.total_loss > 0 else float('inf')
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_pnl': self.total_profit - self.total_loss,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'profit_factor': profit_factor,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl
        }
