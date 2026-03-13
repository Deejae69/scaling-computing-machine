"""
MetaTrader 5 Trading Bot
Main bot implementation with MT5 API integration
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

from config import Config
from indicators import Indicators
from strategy import Strategy
from risk_manager import RiskManager
from position_manager import PositionManager
from trade_journal import TradeJournal
from telegram_notifier import TelegramNotifier


class MT5Bot:
    """MetaTrader 5 Trading Bot"""

    # Map timeframe strings to MT5 constants once at class level
    _TIMEFRAME_MAP = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1,
    }

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the trading bot
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.indicators = Indicators()
        self.strategy = Strategy(self.config)
        self.risk_manager = RiskManager(self.config)
        
        # Initialize position manager (will be set after connection)
        self.position_manager: Optional[PositionManager] = None
        
        # Initialize trade journal
        if self.config.get('journal.enabled', True):
            journal_dir = self.config.get('journal.output_directory', 'trades')
            self.journal = TradeJournal(output_dir=journal_dir)
            self.logger.info(f"Trade journal enabled, output directory: {journal_dir}")
        else:
            self.journal = None
        
        # Initialize Telegram notifier
        telegram_enabled = self.config.get('notifications.telegram_enabled', False)
        if telegram_enabled:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or self.config.get('notifications.telegram_bot_token')
            chat_id = os.getenv('TELEGRAM_CHAT_ID') or self.config.get('notifications.telegram_chat_id')
            self.notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)
        else:
            self.notifier = TelegramNotifier()  # Disabled notifier
        
        # State tracking
        self.is_running = False
        self.current_position = None
        self.symbol_info = None
        
        self.logger.info("MT5 Bot initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get('logging.level', 'INFO'))
        log_file = self.config.get('logging.file', 'bot.log')
        
        # Create logger
        self.logger = logging.getLogger('MT5Bot')
        self.logger.setLevel(log_level)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        
        # Console handler
        if self.config.get('logging.console', True):
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        
        self.logger.addHandler(fh)
    
    def connect_mt5(self, max_retries: int = 3) -> bool:
        """Connect and login to MetaTrader 5 with retry logic
        
        Args:
            max_retries: Maximum number of connection attempts
            
        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Initialize MT5
                if not mt5.initialize():
                    self.logger.warning(f"MT5 initialize() failed (attempt {attempt}/{max_retries}), "
                                       f"error: {mt5.last_error()}")
                    if attempt < max_retries:
                        time.sleep(2 * attempt)  # Exponential backoff
                        continue
                    return False
                
                self.logger.info("MT5 initialized successfully")
                
                # Login if credentials provided
                if self.config.mt5_login and self.config.mt5_password and self.config.mt5_server:
                    if not mt5.login(
                        login=self.config.mt5_login,
                        password=self.config.mt5_password,
                        server=self.config.mt5_server
                    ):
                        self.logger.warning(f"MT5 login failed (attempt {attempt}/{max_retries}), "
                                          f"error: {mt5.last_error()}")
                        mt5.shutdown()
                        if attempt < max_retries:
                            time.sleep(2 * attempt)
                            continue
                        return False
                    
                    self.logger.info(f"Logged in to MT5 account: {self.config.mt5_login}")
                
                # Get account info
                account_info = mt5.account_info()
                if account_info is None:
                    self.logger.warning(f"Failed to get account info (attempt {attempt}/{max_retries})")
                    if attempt < max_retries:
                        time.sleep(2 * attempt)
                        continue
                    return False
                
                self.logger.info(f"Account info: Balance={account_info.balance}, "
                                f"Equity={account_info.equity}, Server={account_info.server}")
                
                # Get symbol info
                self.symbol_info = mt5.symbol_info(self.config.symbol)
                if self.symbol_info is None:
                    self.logger.warning(f"Failed to get symbol info for {self.config.symbol} "
                                      f"(attempt {attempt}/{max_retries})")
                    if attempt < max_retries:
                        time.sleep(2 * attempt)
                        continue
                    return False
                
                # Enable symbol if not visible
                if not self.symbol_info.visible:
                    if not mt5.symbol_select(self.config.symbol, True):
                        self.logger.warning(f"Failed to select symbol {self.config.symbol} "
                                          f"(attempt {attempt}/{max_retries})")
                        if attempt < max_retries:
                            time.sleep(2 * attempt)
                            continue
                        return False
                
                self.logger.info(f"Symbol {self.config.symbol} loaded successfully")
                
                # Initialize position manager
                self.position_manager = PositionManager(
                    symbol=self.config.symbol,
                    point=self.symbol_info.point,
                    magic_number=self.config.magic_number
                )
                self.logger.info("Position manager initialized")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Connection error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    continue
                return False
        
        return False
    
    def disconnect_mt5(self):
        """Disconnect from MetaTrader 5"""
        mt5.shutdown()
        self.logger.info("MT5 connection closed")
    
    def get_timeframe(self) -> int:
        """Convert timeframe string to MT5 constant
        
        Returns:
            MT5 timeframe constant
        """
        return self._TIMEFRAME_MAP.get(self.config.timeframe_str, mt5.TIMEFRAME_M5)
    
    def fetch_data(self) -> Optional[pd.DataFrame]:
        """Fetch historical data from MT5
        
        Returns:
            DataFrame with OHLC data or None if failed
        """
        timeframe = self.get_timeframe()
        
        # Fetch rates
        rates = mt5.copy_rates_from_pos(
            self.config.symbol,
            timeframe,
            0,
            self.config.lookback_bars
        )
        
        if rates is None or len(rates) == 0:
            self.logger.error("Failed to fetch rates from MT5")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Add indicators
        df = self.indicators.add_all_indicators(
            df,
            ema_fast=self.strategy.ema_fast_period,
            ema_slow=self.strategy.ema_slow_period,
            rsi_period=self.strategy.rsi_period,
            atr_period=self.strategy.atr_period
        )
        
        self.logger.debug(f"Fetched {len(df)} bars of data")
        
        return df
    
    def get_spread_points(self) -> float:
        """Get current spread in points
        
        Returns:
            Spread in points
        """
        tick = mt5.symbol_info_tick(self.config.symbol)
        if tick is None:
            self.logger.warning("Failed to get tick info")
            return float('inf')
        
        spread_points = (tick.ask - tick.bid) / self.symbol_info.point
        return spread_points
    
    def get_current_position(self) -> Optional[Dict[str, Any]]:
        """Get current open position for this symbol
        
        Returns:
            Position dict or None if no position
        """
        positions = mt5.positions_get(symbol=self.config.symbol)
        
        if positions is None or len(positions) == 0:
            return None
        
        # Filter by magic number
        for pos in positions:
            if pos.magic == self.config.magic_number:
                return {
                    'ticket': pos.ticket,
                    'type': 'long' if pos.type == mt5.ORDER_TYPE_BUY else 'short',
                    'volume': pos.volume,
                    'price': pos.price_open,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit
                }
        
        return None
    
    def open_position(self, signal: str, df: pd.DataFrame) -> bool:
        """Open a new position
        
        Args:
            signal: 'long' or 'short'
            df: DataFrame with indicators
            
        Returns:
            True if order successful, False otherwise
        """
        # Get current prices
        tick = mt5.symbol_info_tick(self.config.symbol)
        if tick is None:
            self.logger.error("Failed to get tick data")
            return False
        
        # Get current ATR
        current_atr = df.iloc[-1]['atr']
        
        # Get account equity
        account_info = mt5.account_info()
        if account_info is None:
            self.logger.error("Failed to get account info")
            return False
        
        # Calculate position size
        volume = self.risk_manager.calculate_position_size(
            equity=account_info.equity,
            atr_value=current_atr,
            point=self.symbol_info.point,
            volume_min=self.symbol_info.volume_min,
            volume_max=self.symbol_info.volume_max,
            volume_step=self.symbol_info.volume_step
        )
        
        # Determine order type and prices
        if signal == 'long':
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            sl = self.risk_manager.calculate_stop_loss(
                price, current_atr, self.symbol_info.point, 'long'
            )
            tp = self.risk_manager.calculate_take_profit(price, sl, 'long')
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            sl = self.risk_manager.calculate_stop_loss(
                price, current_atr, self.symbol_info.point, 'short'
            )
            tp = self.risk_manager.calculate_take_profit(price, sl, 'short')
        
        self.logger.info(f"Opening {signal} position: volume={volume}, "
                        f"price={price}, SL={sl}, TP={tp}")
        
        # Try different filling types in order of preference
        filling_types = [
            mt5.ORDER_FILLING_IOC,
            mt5.ORDER_FILLING_FOK,
            mt5.ORDER_FILLING_RETURN
        ]
        
        for filling_type in filling_types:
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': self.config.symbol,
                'volume': volume,
                'type': order_type,
                'price': price,
                'sl': sl,
                'tp': tp,
                'deviation': self.config.get('execution.slippage_points', 10),
                'magic': self.config.magic_number,
                'comment': f'MT5Bot_{signal}',
                'type_filling': filling_type,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.warning(f"Order send failed with filling type {filling_type}")
                continue
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Order successful: ticket={result.order}, "
                                f"volume={result.volume}, price={result.price}, filling={filling_type}")
                self.risk_manager.reset_order_errors()
                
                # Record in trade journal
                if self.journal:
                    self.journal.start_trade(
                        ticket=result.order,
                        symbol=self.config.symbol,
                        trade_type=signal,
                        volume=result.volume,
                        entry_price=result.price,
                        stop_loss=sl,
                        take_profit=tp
                    )
                
                # Send notification
                self.notifier.notify_trade_open(
                    symbol=self.config.symbol,
                    trade_type=signal,
                    volume=result.volume,
                    price=result.price,
                    sl=sl,
                    tp=tp
                )
                
                # Activate trailing stop if enabled
                if self.config.enable_trailing_stop and self.position_manager:
                    trailing_distance = self.config.get('execution.trailing_stop_distance', 50)
                    self.position_manager.activate_trailing_stop(result.order, trailing_distance)
                
                return True
            
            self.logger.warning(f"Order failed with {filling_type}: {result.retcode} - {result.comment}")
        
        # All filling types failed
        self.logger.error(f"Order failed with all filling types")
        self.risk_manager.record_order_error()
        return False
    
    def close_position(self, position: Dict[str, Any]) -> bool:
        """Close an open position
        
        Args:
            position: Position dictionary
            
        Returns:
            True if close successful, False otherwise
        """
        tick = mt5.symbol_info_tick(self.config.symbol)
        if tick is None:
            self.logger.error("Failed to get tick data")
            return False
        
        # Determine close order type and price
        if position['type'] == 'long':
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': self.config.symbol,
            'volume': position['volume'],
            'type': order_type,
            'position': position['ticket'],
            'price': price,
            'deviation': self.config.get('execution.slippage_points', 10),
            'magic': self.config.magic_number,
            'comment': 'MT5Bot_close',
            'type_filling': mt5.ORDER_FILLING_IOC,
        }
        
        self.logger.info(f"Closing {position['type']} position: ticket={position['ticket']}")
        
        result = mt5.order_send(request)
        
        if result is None:
            self.logger.error("Close order failed: result is None")
            self.risk_manager.record_order_error()
            return False
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"Close failed: {result.retcode} - {result.comment}")
            self.risk_manager.record_order_error()
            return False
        
        self.logger.info(f"Position closed successfully: profit={position['profit']}")
        self.risk_manager.record_trade_result(position['profit'])
        self.risk_manager.reset_order_errors()
        
        # Record in trade journal
        if self.journal:
            self.journal.end_trade(
                exit_price=price,
                pnl=position['profit'],
                exit_reason='strategy_exit'
            )
        
        # Send notification
        self.notifier.notify_trade_close(
            symbol=self.config.symbol,
            trade_type=position['type'],
            pnl=position['profit'],
            reason='strategy_exit'
        )
        
        # Clean up position manager tracking
        if self.position_manager:
            self.position_manager.cleanup_closed_position(position['ticket'])
        
        return True
    
    def process_tick(self):
        """Process one iteration of the trading logic"""
        # Fetch current data
        df = self.fetch_data()
        if df is None:
            return
        
        # Get account equity
        account_info = mt5.account_info()
        if account_info is None:
            self.logger.error("Failed to get account info")
            return
        
        # Check if trading is allowed
        can_trade, reason = self.risk_manager.can_trade(account_info.equity)
        if not can_trade:
            self.logger.warning(f"Trading disabled: {reason}")
            self.notifier.notify_kill_switch(reason)
            return
        
        # Get current spread
        spread = self.get_spread_points()
        
        # Check for existing position
        position = self.get_current_position()
        
        if position is not None:
            # Update trailing stop if enabled
            if self.config.enable_trailing_stop and self.position_manager:
                tick = mt5.symbol_info_tick(self.config.symbol)
                if tick:
                    current_price = tick.bid if position['type'] == 'long' else tick.ask
                    self.position_manager.update_trailing_stop(
                        ticket=position['ticket'],
                        current_price=current_price,
                        position_type=position['type'],
                        current_sl=position['sl']
                    )
            
            # We have an open position, check if we should close it
            if self.strategy.should_close_position(df, position['type']):
                self.logger.info(f"Strategy signal to close {position['type']} position")
                self.close_position(position)
        else:
            # No open position, check for entry signals
            signal = self.strategy.get_signal(df, spread)
            
            if signal is not None:
                self.logger.info(f"Strategy signal: {signal}")
                self.open_position(signal, df)
    
    def run(self, interval_seconds: int = 60):
        """Run the trading bot in a loop
        
        Args:
            interval_seconds: Sleep interval between iterations
        """
        if not self.connect_mt5(max_retries=self.config.get('execution.connection_retries', 3)):
            self.logger.error("Failed to connect to MT5")
            return
        
        self.is_running = True
        self.logger.info("Bot started. Press Ctrl+C to stop.")
        
        iteration_count = 0
        heartbeat_interval = self.config.get('execution.heartbeat_interval', 10)
        
        try:
            while self.is_running:
                try:
                    iteration_count += 1
                    
                    # Heartbeat log
                    if iteration_count % heartbeat_interval == 0:
                        account_info = mt5.account_info()
                        if account_info:
                            stats = self.risk_manager.get_statistics()
                            self.logger.info(f"Heartbeat: Equity={account_info.equity:.2f}, "
                                           f"Balance={account_info.balance:.2f}, "
                                           f"Trades={stats['total_trades']}, "
                                           f"Win%={stats['win_rate']:.1f}, "
                                           f"Net P&L={stats['net_pnl']:.2f}")
                    
                    self.process_tick()
                except Exception as e:
                    self.logger.error(f"Error in process_tick: {e}", exc_info=True)
                
                # Sleep until next iteration
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        finally:
            # Print final statistics
            stats = self.risk_manager.get_statistics()
            self.logger.info("=" * 60)
            self.logger.info("FINAL TRADING STATISTICS")
            self.logger.info("=" * 60)
            self.logger.info(f"Total Trades: {stats['total_trades']}")
            self.logger.info(f"Winning Trades: {stats['winning_trades']}")
            self.logger.info(f"Losing Trades: {stats['losing_trades']}")
            self.logger.info(f"Win Rate: {stats['win_rate']:.2f}%")
            self.logger.info(f"Total Profit: {stats['total_profit']:.2f}")
            self.logger.info(f"Total Loss: {stats['total_loss']:.2f}")
            self.logger.info(f"Net P&L: {stats['net_pnl']:.2f}")
            if stats['total_trades'] > 0:
                self.logger.info(f"Average Win: {stats['average_win']:.2f}")
                self.logger.info(f"Average Loss: {stats['average_loss']:.2f}")
                if stats['profit_factor'] != float('inf'):
                    self.logger.info(f"Profit Factor: {stats['profit_factor']:.2f}")
            self.logger.info("=" * 60)
            
            # Export trade journal if enabled
            if self.journal and self.config.get('journal.export_on_shutdown', True):
                try:
                    csv_path = self.journal.export_csv()
                    json_path = self.journal.export_json()
                    self.logger.info(f"Trade journal exported to:")
                    self.logger.info(f"  CSV: {csv_path}")
                    self.logger.info(f"  JSON: {json_path}")
                    
                    journal_stats = self.journal.get_summary()
                    self.logger.info(f"Journal Summary: {journal_stats['total_trades']} trades recorded")
                except Exception as e:
                    self.logger.error(f"Failed to export trade journal: {e}")
            
            # Send final notification
            if stats['total_trades'] > 0:
                self.notifier.notify_daily_summary(
                    trades=stats['total_trades'],
                    wins=stats['winning_trades'],
                    losses=stats['losing_trades'],
                    pnl=stats['net_pnl'],
                    win_rate=stats['win_rate']
                )
            
            self.disconnect_mt5()
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False


if __name__ == "__main__":
    # Create and run bot
    bot = MT5Bot()
    
    # Run with 60 second intervals (check every minute for M5 timeframe)
    bot.run(interval_seconds=60)
