import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config.settings import Settings
from typing import Dict, List

class TelegramNotifier:
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or Settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or Settings.TELEGRAM_CHAT_ID
        
        # Check if token/chat_id are actually configured (not placeholder values)
        token_configured = self.token and self.token != 'your_telegram_bot_token'
        chat_configured = self.chat_id and self.chat_id != 'your_chat_id'
        
        if token_configured and chat_configured:
            self.bot = Bot(token=self.token)
            self.enabled = True
        else:
            self.bot = None
            self.enabled = False
    
    async def send_message(self, message: str):
        """Send a message to Telegram"""
        if not self.enabled:
            return
        
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
        except TelegramError as e:
            print(f"Telegram error: {e}")
    
    def send_sync(self, message: str):
        """Send message synchronously"""
        if not self.enabled:
            return
        
        try:
            asyncio.run(self.send_message(message))
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
    
    def _format_balance_info(self, balance_info: Dict) -> str:
        """Format balance information with asset breakdown"""
        if not balance_info or balance_info.get('total', 0) == 0:
            return ""
        
        # Check if futures or spot
        is_futures = any(a.get('unrealized_pnl') is not None for a in balance_info.get('assets', []))
        
        if is_futures:
            # Futures balance display
            text = f"\n\n💰 *Account Balance*"
            text += f"\n┣ Equity: `${balance_info['total']:.2f}`"
            text += f"\n┣ Available: `${balance_info['available']:.2f}`"
            text += f"\n┗ Used: `${balance_info['locked']:.2f}`"
            
            # Show unrealized PnL if any
            for asset in balance_info.get('assets', []):
                if asset.get('unrealized_pnl', 0) != 0:
                    pnl = asset['unrealized_pnl']
                    emoji = "📈" if pnl > 0 else "📉"
                    text += f"\n  {emoji} Unrealized PnL: `${pnl:.2f}`"
        else:
            # Spot balance display with asset breakdown
            text = f"\n\n💰 *Account Balance* (Total: `${balance_info['total']:.2f}`)"
            
            assets = balance_info.get('assets', [])
            if assets:
                # Sort by USD value descending
                sorted_assets = sorted(assets, key=lambda x: x['usd_value'], reverse=True)
                
                for asset in sorted_assets[:5]:  # Show top 5 assets
                    asset_name = asset['asset']
                    total_amount = asset['free'] + asset['locked']
                    usd_value = asset['usd_value']
                    
                    if asset_name == 'USDT':
                        text += f"\n┣ {asset_name}: `${total_amount:.2f}`"
                    else:
                        text += f"\n┣ {asset_name}: `{total_amount:.4f}` (`${usd_value:.2f}`)"
                
                if len(assets) > 5:
                    text += f"\n┗ +{len(assets) - 5} more assets"
                else:
                    # Change last item connector
                    text = text.replace("┣", "┗", text.count("┣"))
        
        return text
    
    def notify_entry(self, trade_info: Dict, balance: float = None, balance_info: Dict = None):
        """Send entry notification"""
        balance_text = self._format_balance_info(balance_info) if balance_info else (
            f"\n💰 Balance: `${balance:.2f}` USDT" if balance is not None else ""
        )
        
        message = f"""
🟢 *ENTRY SIGNAL*

Symbol: `{trade_info['symbol']}`
Direction: *{trade_info['direction'].upper()}*
Entry Price: `{trade_info['entry_price']:.6f}`
Position Size: `{trade_info['position_size']:.4f}`
Stop Loss: `{trade_info['stop_loss']:.6f}`

Take Profits:
• TP1: `{trade_info['take_profits']['tp1']:.6f}`
• TP2: `{trade_info['take_profits']['tp2']:.6f}`
• TP3: `{trade_info['take_profits']['tp3']:.6f}`

Reason: {trade_info['signal']['reason']}
Timeframe: {trade_info['signal']['timeframe']}{balance_text}
"""
        self.send_sync(message)
    
    def notify_exit(self, symbol: str, exit_type: str, price: float, pnl: float, balance: float = None, balance_info: Dict = None):
        """Send exit notification"""
        emoji = "🟢" if pnl > 0 else "🔴"
        balance_text = self._format_balance_info(balance_info) if balance_info else (
            f"\n💰 Balance: `${balance:.2f}` USDT" if balance is not None else ""
        )
        
        message = f"""
{emoji} *{exit_type.upper()}*

Symbol: `{symbol}`
Exit Price: `{price:.6f}`
PnL: `{pnl:.2f}` USDT{balance_text}
"""
        self.send_sync(message)
    
    def notify_stop_loss(self, symbol: str, price: float, pnl: float, balance: float = None, balance_info: Dict = None):
        """Send stop loss notification"""
        balance_text = self._format_balance_info(balance_info) if balance_info else (
            f"\n💰 Balance: `${balance:.2f}` USDT" if balance is not None else ""
        )
        
        message = f"""
🛑 *STOP LOSS HIT*

Symbol: `{symbol}`
Stop Price: `{price:.6f}`
Loss: `{pnl:.2f}` USDT{balance_text}
"""
        self.send_sync(message)
    
    def notify_error(self, error_msg: str):
        """Send error notification"""
        message = f"""
⚠️ *ERROR*

{error_msg}
"""
        self.send_sync(message)
    
    def notify_daily_summary(self, trades: int, pnl: float, win_rate: float, balance: float = None, balance_info: Dict = None):
        """Send daily summary"""
        emoji = "📈" if pnl > 0 else "📉"
        balance_text = self._format_balance_info(balance_info) if balance_info else (
            f"\n💰 Balance: `${balance:.2f}` USDT" if balance is not None else ""
        )
        
        message = f"""
{emoji} *DAILY SUMMARY*

Total Trades: {trades}
Total PnL: `{pnl:.2f}` USDT
Win Rate: {win_rate:.1f}%{balance_text}
"""
        self.send_sync(message)
