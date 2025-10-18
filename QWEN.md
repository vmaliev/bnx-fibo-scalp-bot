# Project Context: Fibo Scalp Bot for BingX

## Project Overview

The Fibo Scalp Bot is a sophisticated cryptocurrency trading bot that uses Fibonacci retracement levels and multi-timeframe analysis for automated trading on the BingX exchange. The bot is designed for scalping strategies, focusing on quick trades that capitalize on short-term market movements.

### Key Features
- **Multi-Timeframe Analysis**: Uses 1H, 15m, 5m, and 1m charts for trend confirmation
- **Fibonacci Retracement**: Automatically detects swing points and calculates Fibo levels
- **Risk Management**: Configurable risk percentage per trade with automatic stop-loss and take-profit levels
- **Staged Exits**: Partial profit-taking at multiple Fibonacci extension levels
- **Trailing Stop**: Moves stop to breakeven after first target is hit
- **Daily Limits**: Configurable max trades and loss limits per day
- **Telegram Notifications**: Real-time alerts for entries, exits, and errors
- **CSV Logging**: Detailed trade history for analysis
- **Backtesting**: Test strategies on historical data before going live
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Architecture and Components

The bot follows a modular architecture with the following key components:

- **bot.py**: Main entry point that orchestrates the trading loop
- **core/data_fetcher.py**: Handles market data acquisition and technical indicators
- **core/strategy.py**: Implements the Fibo scalp trading strategy logic
- **core/risk_manager.py**: Manages position sizing, order execution, and risk controls
- **core/telegram_notifier.py**: Handles Telegram notifications
- **core/logger.py**: Logs trades to CSV and console
- **config/settings.py**: Centralized configuration management
- **core/backtester.py**: Backtesting engine for strategy validation

## Strategy Logic

The bot follows a multi-step strategy:
1. **Trend Filter**: Analyzes 1H and 15m charts to identify market conditions
2. **Impulse Detection**: Looks for fast price moves on 5m and 1m charts
3. **Fibonacci Retracement**: Waits for pullback into specific Fibo zones
4. **Entry Confirmation**: Uses RSI reversal or candle pattern confirmation
5. **Entry Trigger**: Executes entry based on breakout or immediate entry
6. **Stop Loss**: Placed beyond 0.786 Fibonacci level
7. **Take Profit**: Staged exits at 0.236 / 0.0 / 1.272 extensions

## Trading Types

The bot supports both:
- **Spot Trading**: Direct buying/selling of cryptocurrencies
- **Futures Trading**: Leveraged trading with configurable leverage

## Building and Running

### Prerequisites
- Python 3.11+
- BingX account with API keys
- (Optional) Telegram bot token for notifications

### Setup Commands
```bash
# Navigate to project directory
cd /Users/slava/bnx-fibo-scalp-bot-qwen

# Run automated setup
./setup.sh

# Add BingX API credentials
./add_api_keys.sh

# Or manually edit .env file
nano .env
```

### Running the Bot
```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot in live mode
python bot.py

# Or use the start script
./start_bot.sh

# Check balance before running
python check_balance.py
```

### Backtesting
```bash
python -m core.backtester
```

### Docker Deployment
```bash
cd docker
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

## Configuration

All settings are managed in `.env` file:
- Trading parameters: symbol, risk percentage, daily limits
- Strategy parameters: EMA periods, RSI levels, Fibonacci zones
- Timeframes: which timeframes to use for analysis
- API endpoints: testnet vs mainnet URLs
- Telegram: bot token and chat ID for notifications

Key settings:
- `TRADING_MODE`: 'testnet' or 'mainnet'
- `TRADING_TYPE`: 'spot' or 'futures'
- `LEVERAGE`: Leverage for futures trading (1-125)
- `RISK_PERCENT`: Risk per trade (default 10%)
- `SYMBOL`: Trading symbol (default 'BTC-USDT')

## Development Conventions

- The code uses a risk management system that enforces position sizing based on account balance and stop loss distance
- All external API calls are handled through the BingXClient wrapper
- Logging is done both to console and CSV files for trade analysis
- The bot implements proper signal handling for graceful shutdown
- Error handling is implemented throughout to maintain bot stability

## Important Files

- `README.md`: Main documentation with setup instructions
- `.env.template`: Template for environment variables
- `requirements.txt`: Python dependencies
- `start_bot.sh`: Convenience script to start the bot after checking balance
- `API_SETUP.md`: Detailed instructions for setting up BingX API keys

## Risk Warning

**IMPORTANT**: Trading cryptocurrencies involves substantial risk of loss. This bot is provided for educational purposes only. Always:
- Start with testnet mode to verify functionality
- Use small position sizes when testing live
- Never risk more than you can afford to lose
- Monitor the bot regularly
- Understand the strategy before deploying

## Current Branch Information

The repository has multiple branches including:
- `main`: Main production branch
- `telegram-integration`: Integration with Telegram bot features
- `futures`: Futures trading implementation (current branch)
- `bnxfiboscalpgemini`: BingX Fibo Scalp strategy implementation

## Specialized Strategies

The bot includes several specialized strategies and configurations:
- **RELAXED_MODE**: Wider entry zones and more flexible RSI thresholds
- **ULTRA_AGGRESSIVE**: More frequent signals with wider entry zones
- **SIDWAYS/RANGING**: Market strategy for non-trending conditions

The bot is currently configured for sideways/ranging market conditions, with the strategy focusing on this type of market environment.