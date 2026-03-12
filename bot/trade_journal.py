"""
Trade journal for recording and exporting trade history
"""
import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class TradeJournal:
    """Records and exports trade history to CSV and JSON"""
    
    def __init__(self, output_dir: str = "trades"):
        """Initialize trade journal
        
        Args:
            output_dir: Directory to save trade records
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.trades: List[Dict[str, Any]] = []
        self.current_trade: Optional[Dict[str, Any]] = None
        
    def start_trade(self, 
                   ticket: int,
                   symbol: str,
                   trade_type: str,
                   volume: float,
                   entry_price: float,
                   stop_loss: float,
                   take_profit: float,
                   timestamp: Optional[datetime] = None) -> None:
        """Record trade entry
        
        Args:
            ticket: Order ticket number
            symbol: Trading symbol
            trade_type: 'long' or 'short'
            volume: Position size in lots
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            timestamp: Entry timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        self.current_trade = {
            'ticket': ticket,
            'symbol': symbol,
            'type': trade_type,
            'volume': volume,
            'entry_price': entry_price,
            'entry_time': timestamp.isoformat(),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_price': None,
            'exit_time': None,
            'pnl': None,
            'exit_reason': None,
            'duration_minutes': None
        }
    
    def end_trade(self,
                 exit_price: float,
                 pnl: float,
                 exit_reason: str = 'unknown',
                 timestamp: Optional[datetime] = None) -> None:
        """Record trade exit
        
        Args:
            exit_price: Exit price
            pnl: Profit/loss amount
            exit_reason: Reason for exit (e.g., 'stop_loss', 'take_profit', 'signal')
            timestamp: Exit timestamp (defaults to now)
        """
        if self.current_trade is None:
            return
            
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate duration
        entry_time = datetime.fromisoformat(self.current_trade['entry_time'])
        duration = (timestamp - entry_time).total_seconds() / 60
        
        self.current_trade.update({
            'exit_price': exit_price,
            'exit_time': timestamp.isoformat(),
            'pnl': pnl,
            'exit_reason': exit_reason,
            'duration_minutes': round(duration, 2)
        })
        
        self.trades.append(self.current_trade.copy())
        self.current_trade = None
    
    def export_csv(self, filename: Optional[str] = None) -> str:
        """Export trades to CSV file
        
        Args:
            filename: Output filename (defaults to trades_YYYYMMDD.csv)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        if not self.trades:
            return str(filepath)
        
        fieldnames = list(self.trades[0].keys())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.trades)
        
        return str(filepath)
    
    def export_json(self, filename: Optional[str] = None) -> str:
        """Export trades to JSON file
        
        Args:
            filename: Output filename (defaults to trades_YYYYMMDD.json)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.trades, f, indent=2)
        
        return str(filepath)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all trades
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_duration': 0.0
            }
        
        winning = [t for t in self.trades if t['pnl'] > 0]
        losing = [t for t in self.trades if t['pnl'] < 0]
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'total_pnl': sum(t['pnl'] for t in self.trades),
            'avg_win': sum(t['pnl'] for t in winning) / len(winning) if winning else 0.0,
            'avg_loss': sum(t['pnl'] for t in losing) / len(losing) if losing else 0.0,
            'avg_duration': sum(t['duration_minutes'] for t in self.trades) / len(self.trades)
        }
