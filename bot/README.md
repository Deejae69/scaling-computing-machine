# MetaTrader 5 Trading Bot

A Python trading bot for MetaTrader 5 implementing an EMA crossover strategy with RSI and ATR filters.

## Features

### Core Strategy
- **Strategy**: EMA(20/50) crossover with RSI(14) filter and ATR(14) volatility check
- **Risk Management**: 
  - 1% equity risk per trade
  - ATR-based stop loss (1.8x ATR)
  - Risk-reward ratio of 1.7:1
  - Daily loss cap (2.5%)
  - Consecutive loss kill switch (3 losses)
  - Order error protection
- **Modes**: Backtest (planned), Paper/Demo trading, Live trading
- **Spread filtering**: Skips trades if spread exceeds threshold
- **Automated position sizing**: Based on ATR and account equity

### New Features ✨
- **🎯 Trailing Stops**: Automatically locks in profits as trade moves favorably
- **📊 Trade Journal**: Records all trades with CSV/JSON export for analysis
- **📱 Telegram Notifications**: Real-time alerts for trades, errors, and daily summaries
- **⚙️ Advanced Position Management**: Modify stop loss and take profit on open positions
- **📈 Enhanced Statistics**: Comprehensive performance tracking and reporting

See [NEW_FEATURES.md](NEW_FEATURES.md) for detailed documentation on new features.

## Requirements

- Python 3.11+
- MetaTrader 5 terminal installed
- MT5 account (demo or live)
- (Optional) Telegram account for notifications

## Installation

1. Install Python dependencies:
```bash
cd bot
pip install -r requirements.txt
```

2. Configure your MT5 credentials:

Create a `.env` file in the bot directory:
```bash
MT5_LOGIN=your_login_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

3. Configure trading parameters:

Edit `config.yaml` to adjust:
- Symbol and timeframe
- Risk parameters
- Strategy indicators
- Trading mode (paper_trade, live_trade)

## Configuration

### Trading Parameters
- `symbol`: Trading symbol (default: EURUSD)
- `timeframe`: M5, M15, M30, H1, etc.
- `max_spread_points`: Maximum acceptable spread

### Risk Management
- `equity_risk_percent`: 1% risk per trade
- `daily_loss_cap_percent`: Stop trading after -2.5% daily loss
- `max_consecutive_losses`: Kill switch after 3 consecutive losses
- `atr_stop_multiplier`: Stop loss = ATR × 1.8
- `risk_reward_ratio`: Take profit = stop loss × 1.7

### Strategy Indicators
- `ema_fast_period`: 20 (fast EMA)
- `ema_slow_period`: 50 (slow EMA)
- `rsi_period`: 14
- `rsi_min/max`: 40-60 (RSI range filter)
- `atr_period`: 14
- `atr_volatility_threshold`: 0.8 (ATR must be > 80% of mean)

## Usage

### Demo/Paper Trading (Recommended to Start)

1. Set mode in `config.yaml`:
```yaml
mode:
  paper_trade: true
  live_trade: false
```

2. Run the bot:
```bash
python mt5_bot.py
```

### Live Trading (Use with Caution)

⚠️ **WARNING**: Only use live trading after thorough testing on a demo account!

1. Set mode in `config.yaml`:
```yaml
mode:
  paper_trade: false
  live_trade: true
```

2. Run the bot:
```bash
python mt5_bot.py
```

## Trading Logic

### Entry Conditions (Long)
1. Fast EMA crosses above Slow EMA (bullish crossover)
2. RSI between 40-60 (not overbought/oversold)
3. ATR > 80% of rolling mean (sufficient volatility)
4. Spread ≤ maximum threshold

### Entry Conditions (Short)
1. Fast EMA crosses below Slow EMA (bearish crossover)
2. RSI between 40-60
3. ATR > 80% of rolling mean
4. Spread ≤ maximum threshold

### Exit Conditions
- Stop Loss: ATR × 1.8 from entry
- Take Profit: Stop Loss × 1.7 (risk-reward ratio)
- Opposite EMA crossover
- Daily loss cap reached
- Consecutive loss limit hit

## Risk Controls

The bot implements multiple safety mechanisms:

1. **Per-Trade Risk**: Limited to 1% of account equity
2. **Position Sizing**: Automatically calculated based on ATR and account size
3. **Daily Loss Cap**: Trading stops after -2.5% daily loss
4. **Consecutive Losses**: Trading stops after 3 consecutive losses
5. **Spread Filter**: No trades if spread exceeds threshold
6. **Order Error Kill Switch**: Stops after 5 consecutive order errors
7. **Minimum Lot Validation**: Respects broker's minimum lot size

## Logging

Logs are written to:
- Console (configurable)
- `bot.log` file

Log levels: DEBUG, INFO, WARNING, ERROR

## Important Notes

### Before Trading Live
1. **Test on demo account first** - Verify strategy performance
2. **Check broker requirements** - Minimum lot size, spread, commissions
3. **Verify symbol availability** - Ensure your broker offers the symbol
4. **Monitor initial trades** - Watch the first few trades carefully
5. **Start with small capital** - The bot is designed for ~$100, but test with minimum first

### Known Limitations
- Requires MT5 terminal to be running
- Works with symbols available on your broker
- Network connectivity issues can affect execution
- Backtesting mode is not yet implemented
- No support for hedging accounts

### Broker Compatibility
- Works with most MT5 brokers
- Requires FOK or IOC order filling support
- Check broker's spread and commission structure

## Troubleshooting

### Connection Issues
- Ensure MT5 terminal is running
- Verify credentials in `.env` file
- Check firewall/antivirus settings

### Order Execution Failures
- Verify minimum lot size with broker
- Check account has sufficient margin
- Ensure symbol is available for trading
- Review spread threshold settings

### No Trades Being Executed
- Check if daily loss cap was hit
- Verify spread is within threshold
- Review indicator values (may not meet entry conditions)
- Check if consecutive loss limit was reached

## File Structure

```
bot/
├── mt5_bot.py          # Main bot implementation
├── config.py           # Configuration loader
├── indicators.py       # Technical indicators
├── strategy.py         # Trading strategy logic
├── risk_manager.py     # Risk management
├── config.yaml         # Bot configuration
├── requirements.txt    # Python dependencies
├── .python-version     # Python version
└── README.md          # This file
```

## Disclaimer

**This trading bot is provided for educational purposes only.**

- Trading involves significant risk of loss
- Past performance does not guarantee future results
- Never trade with money you cannot afford to lose
- The authors are not responsible for any financial losses
- Always test thoroughly on a demo account before live trading
- Consult with a financial advisor before making trading decisions

## Support

For issues, questions, or suggestions, please open an issue in the GitHub repository.

## License

See the main repository LICENSE file.
