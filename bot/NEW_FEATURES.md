# New Features Documentation

## Overview

This document describes the new features added to the MT5 Trading Bot, including trailing stops, trade journaling, and Telegram notifications.

## 1. Trailing Stop Implementation

### Description
Automatically adjusts stop loss to lock in profits as the trade moves favorably. The trailing stop maintains a fixed distance behind the current price and only moves in the profitable direction.

### Configuration
```yaml
risk:
  enable_trailing_stop: true  # Enable/disable trailing stops

execution:
  trailing_stop_distance: 50  # Distance in points to trail behind price
```

### How It Works
1. When a position opens with `enable_trailing_stop: true`, trailing stop is automatically activated
2. The bot monitors the position on each tick
3. As price moves favorably:
   - **Long positions**: Stop loss moves up, never down
   - **Short positions**: Stop loss moves down, never up
4. Stop loss maintains the configured distance from current price
5. If price reverses, the stop loss stays at the most favorable level

### Example
- Long position enters at 1.1000
- Trailing distance: 50 points (0.0050)
- Price moves to 1.1100 → SL moves to 1.1050
- Price moves to 1.1200 → SL moves to 1.1150
- Price reverses to 1.1150 → SL stays at 1.1150 (locked in profit)

### Benefits
- Locks in profits automatically
- No manual monitoring required
- Reduces emotional decision-making
- Maximizes winning trades

## 2. Trade Journal

### Description
Automatically records all trades with entry/exit details and exports to CSV and JSON formats for analysis.

### Configuration
```yaml
journal:
  enabled: true  # Enable trade journal
  export_on_shutdown: true  # Auto-export when bot stops
  output_directory: "trades"  # Where to save files
```

### Features
- **Automatic Recording**: Every trade is logged with:
  - Ticket number
  - Symbol
  - Trade type (long/short)
  - Volume
  - Entry/exit prices
  - Stop loss/take profit
  - P&L
  - Exit reason
  - Duration in minutes
  
- **Export Formats**:
  - CSV: `trades/trades_YYYYMMDD_HHMMSS.csv`
  - JSON: `trades/trades_YYYYMMDD_HHMMSS.json`

- **Summary Statistics**:
  - Total trades
  - Win/loss breakdown
  - Total P&L
  - Average win/loss
  - Average trade duration

### Usage
Journal is automatic when enabled. Files are exported on bot shutdown.

### Example CSV Output
```csv
ticket,symbol,type,volume,entry_price,entry_time,stop_loss,take_profit,exit_price,exit_time,pnl,exit_reason,duration_minutes
12345,EURUSD,long,0.1,1.10000,2024-01-15T10:00:00,1.09500,1.11000,1.10500,2024-01-15T12:30:00,50.00,strategy_exit,150.0
```

## 3. Telegram Notifications

### Description
Receive real-time alerts on your mobile device via Telegram for trades, errors, and daily summaries.

### Setup

1. **Create Telegram Bot**:
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token

2. **Get Your Chat ID**:
   - Message @userinfobot on Telegram
   - Note your chat ID

3. **Configure Bot**:
   ```yaml
   notifications:
     telegram_enabled: true
     telegram_bot_token: "YOUR_BOT_TOKEN"
     telegram_chat_id: "YOUR_CHAT_ID"
   ```

   Or use environment variables (recommended):
   ```bash
   # In .env file
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

### Notification Types

#### Trade Open
```
🟢 Trade Opened
Symbol: EURUSD
Type: LONG
Volume: 0.10 lots
Entry: 1.10000
SL: 1.09500
TP: 1.11000
Time: 2024-01-15 10:00:00
```

#### Trade Close
```
✅ Trade Closed
Symbol: EURUSD
Type: LONG
P&L: +50.00
Reason: strategy_exit
Time: 2024-01-15 12:30:00
```

#### Kill Switch
```
🛑 KILL SWITCH ACTIVATED
Reason: Max consecutive losses reached (3)
Trading stopped!
Time: 2024-01-15 14:00:00
```

#### Daily Summary
```
📊 Daily Summary
Trades: 5
Wins: 3 | Losses: 2
Win Rate: 60.0%
💰 P&L: +125.50
Date: 2024-01-15
```

#### Error Alerts
```
⚠️ Bot Error
Failed to connect to MT5
Time: 2024-01-15 09:00:00
```

### Benefits
- **Real-time monitoring** without watching charts
- **Instant alerts** for critical events
- **Mobile accessibility** from anywhere
- **Peace of mind** knowing you're informed

## 4. Position Manager

### Description
Advanced position management system for modifying open positions.

### Features
- **Modify SL/TP**: Change stop loss and/or take profit on open positions
- **Trailing Stop Management**: Internal tracking and updates
- **Position Tracking**: Monitors profit levels and trailing state

### API Usage
```python
# Modify position
position_manager.modify_position(
    ticket=12345,
    new_sl=1.09800,
    new_tp=1.11500
)

# Activate trailing stop manually
position_manager.activate_trailing_stop(
    ticket=12345,
    trailing_distance_points=50
)

# Update trailing stop
position_manager.update_trailing_stop(
    ticket=12345,
    current_price=1.10500,
    position_type='long',
    current_sl=1.09500
)
```

## Installation & Requirements

### New Dependencies
```bash
pip install requests>=2.31.0  # For Telegram (optional)
```

### Configuration Changes
Update your `config.yaml` with new sections:
```yaml
# Add to execution section
execution:
  trailing_stop_distance: 50

# Add notifications section
notifications:
  telegram_enabled: false
  telegram_bot_token: ""
  telegram_chat_id: ""

# Add journal section
journal:
  enabled: true
  export_on_shutdown: true
  output_directory: "trades"
```

## Testing

### Test Trailing Stop
1. Enable trailing stop in config
2. Run bot on demo account
3. Enter a trade
4. Watch logs for "Trailing stop activated" and "Trailing stop updated"
5. Verify SL moves with price in favorable direction

### Test Trade Journal
1. Enable journal in config
2. Run bot and execute some trades
3. Stop bot
4. Check `trades/` directory for CSV and JSON files
5. Verify all trade details are recorded

### Test Telegram Notifications
1. Set up bot with @BotFather
2. Add credentials to .env
3. Enable in config
4. Start bot
5. Execute a test trade
6. Check Telegram for notifications

## Troubleshooting

### Telegram Not Working
- Verify bot token and chat ID are correct
- Check internet connection
- Ensure `requests` library is installed
- Check logs for error messages

### Journal Not Exporting
- Verify `journal.enabled: true` in config
- Check write permissions on output directory
- Review logs for export errors

### Trailing Stop Not Moving
- Confirm `enable_trailing_stop: true`
- Check that price is moving favorably
- Verify trailing distance is reasonable
- Review logs for update messages

## Best Practices

1. **Start with Demo**: Test all features on demo account first
2. **Monitor Notifications**: Ensure you receive alerts reliably
3. **Review Journal Regularly**: Analyze trade journal for patterns
4. **Adjust Trailing Distance**: Fine-tune based on symbol volatility
5. **Backup Trade Data**: Periodically save exported CSV/JSON files
6. **Test Kill Switches**: Verify notifications work when limits hit

## Performance Impact

- **Trailing Stop**: Minimal (checked on each tick when position open)
- **Trade Journal**: Negligible (simple dictionary operations)
- **Telegram**: Low (asynchronous HTTP requests)

## Security Notes

- **Never commit** .env file with credentials
- **Use environment variables** for sensitive data
- **Restrict bot token access** (only you should have it)
- **Review exported files** before sharing (contains trade details)

## Future Enhancements

Potential additions for future versions:
- Multiple symbol support
- Advanced order types (limit, stop orders)
- Web dashboard
- Machine learning integration
- Backtesting framework
- Email notifications
- Discord integration
