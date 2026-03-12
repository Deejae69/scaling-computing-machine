"""
Notification system for trade alerts via Telegram
"""
import logging
from typing import Optional
from datetime import datetime


class TelegramNotifier:
    """Send notifications via Telegram bot"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize Telegram notifier
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        self.logger = logging.getLogger(__name__)
        
        if self.enabled:
            try:
                import requests
                self.requests = requests
                self.logger.info("Telegram notifications enabled")
            except ImportError:
                self.logger.warning("requests library not installed, Telegram notifications disabled")
                self.enabled = False
        else:
            self.logger.info("Telegram notifications disabled (no credentials)")
    
    def send_message(self, message: str) -> bool:
        """Send a message via Telegram
        
        Args:
            message: Message text to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = self.requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                self.logger.debug("Telegram notification sent successfully")
                return True
            else:
                self.logger.warning(f"Failed to send Telegram notification: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    def notify_trade_open(self, symbol: str, trade_type: str, volume: float, 
                         price: float, sl: float, tp: float) -> bool:
        """Notify about trade opening
        
        Args:
            symbol: Trading symbol
            trade_type: 'long' or 'short'
            volume: Position size
            price: Entry price
            sl: Stop loss
            tp: Take profit
            
        Returns:
            True if sent successfully
        """
        emoji = "🟢" if trade_type.lower() == "long" else "🔴"
        message = (
            f"{emoji} <b>Trade Opened</b>\n"
            f"Symbol: {symbol}\n"
            f"Type: {trade_type.upper()}\n"
            f"Volume: {volume:.2f} lots\n"
            f"Entry: {price:.5f}\n"
            f"SL: {sl:.5f}\n"
            f"TP: {tp:.5f}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)
    
    def notify_trade_close(self, symbol: str, trade_type: str, pnl: float, 
                          reason: str = "unknown") -> bool:
        """Notify about trade closing
        
        Args:
            symbol: Trading symbol
            trade_type: 'long' or 'short'
            pnl: Profit/loss amount
            reason: Reason for closing
            
        Returns:
            True if sent successfully
        """
        emoji = "✅" if pnl > 0 else "❌"
        pnl_str = f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}"
        
        message = (
            f"{emoji} <b>Trade Closed</b>\n"
            f"Symbol: {symbol}\n"
            f"Type: {trade_type.upper()}\n"
            f"P&L: {pnl_str}\n"
            f"Reason: {reason}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)
    
    def notify_daily_summary(self, trades: int, wins: int, losses: int, 
                            pnl: float, win_rate: float) -> bool:
        """Send daily trading summary
        
        Args:
            trades: Total trades
            wins: Winning trades
            losses: Losing trades
            pnl: Total P&L
            win_rate: Win rate percentage
            
        Returns:
            True if sent successfully
        """
        emoji = "📊"
        pnl_emoji = "💰" if pnl > 0 else "📉"
        pnl_str = f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}"
        
        message = (
            f"{emoji} <b>Daily Summary</b>\n"
            f"Trades: {trades}\n"
            f"Wins: {wins} | Losses: {losses}\n"
            f"Win Rate: {win_rate:.1f}%\n"
            f"{pnl_emoji} P&L: {pnl_str}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d')}"
        )
        return self.send_message(message)
    
    def notify_error(self, error_message: str) -> bool:
        """Send error notification
        
        Args:
            error_message: Error description
            
        Returns:
            True if sent successfully
        """
        message = (
            f"⚠️ <b>Bot Error</b>\n"
            f"{error_message}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)
    
    def notify_kill_switch(self, reason: str) -> bool:
        """Notify that kill switch was triggered
        
        Args:
            reason: Reason for kill switch activation
            
        Returns:
            True if sent successfully
        """
        message = (
            f"🛑 <b>KILL SWITCH ACTIVATED</b>\n"
            f"Reason: {reason}\n"
            f"Trading stopped!\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_message(message)
