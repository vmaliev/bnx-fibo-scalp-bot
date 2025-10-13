# Project Overview

This is a Python-based cryptocurrency trading bot that implements a Fibonacci scalping strategy on the BingX exchange. The bot is designed to trade in sideways or ranging markets, using a multi-timeframe analysis to identify trading opportunities.

## Key Features:

*   **Trading Strategy**: The core strategy is based on Fibonacci retracement levels. It identifies swing points, waits for a pullback to the 0.382-0.618 Fibonacci zone, and then looks for a confirmation signal to enter a trade.
*   **Multi-Timeframe Analysis**: The bot uses multiple timeframes (1h, 15m, 5m, 1m) to analyze the market trend and generate trading signals.
*   **Risk Management**: The bot includes a risk management component that calculates the position size based on a predefined risk percentage and sets a stop-loss for each trade.
*   **Telegram Notifications**: The bot can send real-time notifications about its activities (e.g., new trades, errors) to a Telegram channel.
*   **Backtesting**: The project includes a backtesting engine to test the trading strategy on historical data.
*   **Docker Support**: The bot can be easily deployed using Docker and Docker Compose.

## Project Structure:

*   `bot.py`: The main entry point of the application.
*   `core/`: This directory contains the core logic of the bot.
    *   `strategy.py`: Implements the Fibonacci scalping strategy.
    *   `data_fetcher.py`: Fetches market data from the BingX exchange.
    *   `risk_manager.py`: Manages risk and executes trades.
    *   `logger.py`: Logs trading activities.
    *   `telegram_notifier.py`: Sends notifications to Telegram.
    *   `backtester.py`: The backtesting engine.
*   `config/`: This directory contains the configuration files.
    *   `settings.py`: Manages the application settings.
*   `docker/`: This directory contains the Docker-related files.
    *   `Dockerfile`: The Dockerfile for building the bot's image.
    *   `docker-compose.yml`: The Docker Compose file for deploying the bot.
*   `requirements.txt`: The list of Python dependencies.

# Building and Running

## Prerequisites:

*   Python 3.11+
*   BingX API keys
*   Telegram bot token and chat ID

## Setup:

1.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Create a `.env` file from the `.env.template` and fill in your API keys and other settings.

## Running the bot:

*   **Live Trading**:
    ```bash
    python bot.py
    ```
*   **Backtesting**:
    ```bash
    python -m core.backtester
    ```
*   **Docker**:
    ```bash
    cd docker
    docker-compose up -d
    ```

# Development Conventions

*   The project follows a modular structure, with different components separated into different files and directories.
*   The code is well-documented with comments and docstrings.
*   The project uses a `.env` file for configuration, which is a good practice for keeping secrets and other sensitive information out of the codebase.
*   The project uses a `requirements.txt` file to manage its dependencies, which makes it easy to set up the development environment.
