import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of config folder)
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / '.env'

# Load .env file from project root
load_dotenv(ENV_FILE, override=True)

class Settings:
    # BingX API
    BINGX_API_KEY = os.getenv('BINGX_API_KEY')
    BINGX_SECRET_KEY = os.getenv('BINGX_SECRET_KEY')
    TRADING_MODE = os.getenv('TRADING_MODE', 'testnet')
    
    BINGX_API_URL = (
        os.getenv('BINGX_API_URL_TESTNET') if TRADING_MODE == 'testnet' 
        else os.getenv('BINGX_API_URL_MAINNET')
    )
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Trading
    TRADING_TYPE = os.getenv('TRADING_TYPE', 'futures')  # 'spot' or 'futures'
    SYMBOL = os.getenv('SYMBOL', 'BTC-USDT')
    LEVERAGE = int(os.getenv('LEVERAGE', 5))  # Futures leverage (1-125)
    RISK_PERCENT = float(os.getenv('RISK_PERCENT', 10))  # Risk per trade
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', 99))  # Increased to 99 trades per day
    MAX_DAILY_LOSS_PERCENT = float(os.getenv('MAX_DAILY_LOSS_PERCENT', 5))
    
    # Timeframes
    TIMEFRAMES = os.getenv('TIMEFRAMES', '1m,3m,5m,15m,1h').split(',')
    
    # Strategy (RELAXED SETTINGS for more signals)
    EMA_FAST = int(os.getenv('EMA_FAST', 50))
    EMA_SLOW = int(os.getenv('EMA_SLOW', 200))
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', 14))
    RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', 40))  # Relaxed: 40 instead of 30
    RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', 60))  # Relaxed: 60 instead of 70
    SWING_LOOKBACK = int(os.getenv('SWING_LOOKBACK', 20))
    
    # Fibonacci (WIDER ENTRY ZONE for more signals)
    FIBO_ENTRY_MIN = float(os.getenv('FIBO_ENTRY_MIN', 0.236))  # Wider: 0.236 instead of 0.382
    FIBO_ENTRY_MAX = float(os.getenv('FIBO_ENTRY_MAX', 0.786))  # Wider: 0.786 instead of 0.618
    FIBO_STOP_LEVEL = float(os.getenv('FIBO_STOP_LEVEL', 1.0))  # Further: 1.0 instead of 0.786
    
    # Take Profit
    TP1_FIBO = float(os.getenv('TP1_FIBO', 0.236))
    TP2_FIBO = float(os.getenv('TP2_FIBO', 0.0))
    TP3_FIBO = float(os.getenv('TP3_FIBO', 1.272))
    TP1_PERCENT = int(os.getenv('TP1_PERCENT', 30))
    TP2_PERCENT = int(os.getenv('TP2_PERCENT', 40))
    TP3_PERCENT = int(os.getenv('TP3_PERCENT', 30))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
