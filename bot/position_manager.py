"""
Advanced position management including trailing stops and position modification
"""
import MetaTrader5 as mt5
import logging
from typing import Optional, Dict, Any


class PositionManager:
    """Manages advanced position operations like trailing stops"""
    
    def __init__(self, symbol: str, point: float, magic_number: int):
        """Initialize position manager
        
        Args:
            symbol: Trading symbol
            point: Symbol point value
            magic_number: Magic number for position identification
        """
        self.symbol = symbol
        self.point = point
        self.magic_number = magic_number
        self.logger = logging.getLogger(__name__)
        
        # Track trailing stop state
        self.trailing_active = {}  # ticket -> bool
        self.trailing_distance = {}  # ticket -> distance in points
        self.max_profit = {}  # ticket -> max profit in points
    
    def modify_position(self, 
                       ticket: int,
                       new_sl: Optional[float] = None,
                       new_tp: Optional[float] = None) -> bool:
        """Modify stop loss and/or take profit of an open position
        
        Args:
            ticket: Position ticket number
            new_sl: New stop loss price (None to keep current)
            new_tp: New take profit price (None to keep current)
            
        Returns:
            True if modification successful, False otherwise
        """
        # Get current position
        position = None
        positions = mt5.positions_get(ticket=ticket)
        
        if not positions or len(positions) == 0:
            self.logger.error(f"Position {ticket} not found")
            return False
        
        position = positions[0]
        
        # Use current values if not specified
        if new_sl is None:
            new_sl = position.sl
        if new_tp is None:
            new_tp = position.tp
        
        # Prepare modification request
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': ticket,
            'symbol': self.symbol,
            'sl': new_sl,
            'tp': new_tp,
            'magic': self.magic_number
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            self.logger.error(f"Position modification failed: result is None")
            return False
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Position modification failed: {result.retcode} - {result.comment}")
            return False
        
        self.logger.info(f"Position {ticket} modified: SL={new_sl:.5f}, TP={new_tp:.5f}")
        return True
    
    def activate_trailing_stop(self, ticket: int, trailing_distance_points: int) -> None:
        """Activate trailing stop for a position
        
        Args:
            ticket: Position ticket number
            trailing_distance_points: Distance in points to trail behind price
        """
        self.trailing_active[ticket] = True
        self.trailing_distance[ticket] = trailing_distance_points
        self.max_profit[ticket] = 0
        self.logger.info(f"Trailing stop activated for position {ticket}, distance={trailing_distance_points} points")
    
    def update_trailing_stop(self, ticket: int, current_price: float, 
                            position_type: str, current_sl: float) -> bool:
        """Update trailing stop if profit has increased
        
        Args:
            ticket: Position ticket number
            current_price: Current market price
            position_type: 'long' or 'short'
            current_sl: Current stop loss price
            
        Returns:
            True if stop loss was updated, False otherwise
        """
        if ticket not in self.trailing_active or not self.trailing_active[ticket]:
            return False
        
        # Get position info
        positions = mt5.positions_get(ticket=ticket)
        if not positions or len(positions) == 0:
            return False
        
        position = positions[0]
        entry_price = position.price_open
        
        # Calculate current profit in points
        if position_type == 'long':
            profit_points = (current_price - entry_price) / self.point
        else:
            profit_points = (entry_price - current_price) / self.point
        
        # Update max profit
        if ticket not in self.max_profit:
            self.max_profit[ticket] = profit_points
        else:
            self.max_profit[ticket] = max(self.max_profit[ticket], profit_points)
        
        # Calculate new trailing stop level
        trailing_distance = self.trailing_distance[ticket]
        
        if position_type == 'long':
            new_sl = current_price - (trailing_distance * self.point)
            # Only move SL up, never down
            if new_sl > current_sl:
                if self.modify_position(ticket, new_sl=new_sl):
                    self.logger.info(f"Trailing stop updated for long position {ticket}: "
                                   f"SL moved to {new_sl:.5f}")
                    return True
        else:
            new_sl = current_price + (trailing_distance * self.point)
            # Only move SL down, never up
            if new_sl < current_sl or current_sl == 0:
                if self.modify_position(ticket, new_sl=new_sl):
                    self.logger.info(f"Trailing stop updated for short position {ticket}: "
                                   f"SL moved to {new_sl:.5f}")
                    return True
        
        return False
    
    def deactivate_trailing_stop(self, ticket: int) -> None:
        """Deactivate trailing stop for a position
        
        Args:
            ticket: Position ticket number
        """
        if ticket in self.trailing_active:
            self.trailing_active[ticket] = False
            self.logger.info(f"Trailing stop deactivated for position {ticket}")
    
    def cleanup_closed_position(self, ticket: int) -> None:
        """Clean up tracking data for closed position
        
        Args:
            ticket: Position ticket number
        """
        if ticket in self.trailing_active:
            del self.trailing_active[ticket]
        if ticket in self.trailing_distance:
            del self.trailing_distance[ticket]
        if ticket in self.max_profit:
            del self.max_profit[ticket]
