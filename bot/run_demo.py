"""
Example script to run the MT5 trading bot in paper/demo mode
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mt5_bot import MT5Bot


def main():
    """Run the bot in paper trading mode"""
    print("=" * 60)
    print("MT5 Trading Bot - Paper/Demo Mode")
    print("=" * 60)
    print()
    print("Configuration:")
    print("- Symbol: EURUSD")
    print("- Timeframe: M5")
    print("- Strategy: EMA(20/50) crossover + RSI(14) + ATR(14)")
    print("- Risk: 1% per trade, 2.5% daily loss cap")
    print()
    print("Make sure you have:")
    print("1. MT5 terminal running")
    print("2. Demo account credentials in bot/.env file")
    print("3. Configured config.yaml for your preferences")
    print()
    print("Press Ctrl+C to stop the bot")
    print("=" * 60)
    print()
    
    # Create bot instance
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    bot = MT5Bot(config_path=config_path)
    
    # Run bot (checks every 60 seconds)
    bot.run(interval_seconds=60)


if __name__ == "__main__":
    main()
