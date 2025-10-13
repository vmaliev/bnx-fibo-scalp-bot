"""
Telegram Command Handler
Allows bot control via Telegram commands
"""

import asyncio
import threading
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config.settings import Settings
from typing import Callable

class TelegramCommandHandler:
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or Settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or Settings.TELEGRAM_CHAT_ID
        
        # Check if properly configured
        token_configured = self.token and self.token != 'your_telegram_bot_token'
        chat_configured = self.chat_id and self.chat_id != 'your_chat_id'
        
        self.enabled = token_configured and chat_configured
        self.application = None
        self.bot_instance = None
        self.balance_callback = None
        
        # Thread for running bot
        self.bot_thread = None
        self.running = False
    
    def set_bot_instance(self, bot_instance):
        """Set reference to main bot instance"""
        self.bot_instance = bot_instance
    
    def set_balance_callback(self, callback: Callable):
        """Set callback for getting balance info"""
        self.balance_callback = callback
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        keyboard = [
            [
                InlineKeyboardButton("▶️ Start Bot", callback_data='start_bot'),
                InlineKeyboardButton("⏸️ Pause Bot", callback_data='pause_bot')
            ],
            [
                InlineKeyboardButton("💰 Balance", callback_data='show_balance'),
                InlineKeyboardButton("📊 Status", callback_data='show_status')
            ],
            [InlineKeyboardButton("❓ Help", callback_data='show_help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *Fibo Scalp Bot Control Panel*\n\nChoose an action:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button presses"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'start_bot':
            if self.bot_instance and not self.bot_instance.running:
                # Start bot in separate thread
                self.bot_instance.running = True
                threading.Thread(target=self.bot_instance.run_loop, daemon=True).start()
                await query.edit_message_text("✅ *Bot Started!*\n\nThe bot is now monitoring the market.", parse_mode='Markdown')
            else:
                await query.edit_message_text("ℹ️ *Bot is already running*", parse_mode='Markdown')
        
        elif query.data == 'pause_bot':
            if self.bot_instance and self.bot_instance.running:
                self.bot_instance.running = False
                await query.edit_message_text("⏸️ *Bot Paused*\n\nThe bot has stopped monitoring.", parse_mode='Markdown')
            else:
                await query.edit_message_text("ℹ️ *Bot is not running*", parse_mode='Markdown')
        
        elif query.data == 'show_balance':
            if self.balance_callback:
                balance_info = self.balance_callback()
                
                # Format balance message
                if Settings.TRADING_TYPE == 'futures':
                    message = f"""
💰 *Futures Account Balance*

Equity: `${balance_info['total']:.2f}`
Available Margin: `${balance_info['available']:.2f}`
Used Margin: `${balance_info['locked']:.2f}`
"""
                    # Add unrealized PnL
                    for asset in balance_info.get('assets', []):
                        if asset.get('unrealized_pnl', 0) != 0:
                            pnl = asset['unrealized_pnl']
                            emoji = "📈" if pnl > 0 else "📉"
                            message += f"\n{emoji} Unrealized PnL: `${pnl:.2f}`"
                else:
                    message = f"💰 *Spot Account Balance*\n\nTotal: `${balance_info['total']:.2f}`\n"
                    
                    assets = balance_info.get('assets', [])
                    if assets:
                        message += "\n*Assets:*\n"
                        sorted_assets = sorted(assets, key=lambda x: x['usd_value'], reverse=True)
                        
                        for asset in sorted_assets[:10]:  # Show top 10
                            asset_name = asset['asset']
                            total_amount = asset['free'] + asset['locked']
                            usd_value = asset['usd_value']
                            
                            if asset_name == 'USDT':
                                message += f"• {asset_name}: `${total_amount:.2f}`\n"
                            else:
                                message += f"• {asset_name}: `{total_amount:.4f}` (`${usd_value:.2f}`)\n"
                
                await query.edit_message_text(message, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ *Balance info not available*", parse_mode='Markdown')
        
        elif query.data == 'show_status':
            if self.bot_instance:
                status = "🟢 Running" if self.bot_instance.running else "🔴 Stopped"
                message = f"""
📊 *Bot Status*

Status: {status}
Mode: `{Settings.TRADING_MODE}`
Type: `{Settings.TRADING_TYPE}`
"""
                if Settings.TRADING_TYPE == 'futures':
                    message += f"Leverage: `{Settings.LEVERAGE}x`\n"
                
                message += f"Risk per trade: `{Settings.RISK_PERCENT}%`\n"
                message += f"Symbol: `{Settings.SYMBOL}`\n"
                message += f"Max daily trades: `{Settings.MAX_DAILY_TRADES}`"
                
                await query.edit_message_text(message, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ *Status info not available*", parse_mode='Markdown')
        
        elif query.data == 'show_help':
            message = """
❓ *Bot Commands Help*

*Control Commands:*
• `/start` - Show control panel
• `/balance` - Show account balance
• `/status` - Show bot status

*Control Panel Buttons:*
• ▶️ Start Bot - Resume trading
• ⏸️ Pause Bot - Pause trading
• 💰 Balance - View balances
• 📊 Status - View bot status

*About:*
This bot monitors markets and executes trades based on Fibonacci retracement strategy.
"""
            await query.edit_message_text(message, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        if self.balance_callback:
            balance_info = self.balance_callback()
            
            # Format balance message
            if Settings.TRADING_TYPE == 'futures':
                message = f"""
💰 *Futures Account Balance*

Equity: `${balance_info['total']:.2f}`
Available Margin: `${balance_info['available']:.2f}`
Used Margin: `${balance_info['locked']:.2f}`
"""
                # Add unrealized PnL
                for asset in balance_info.get('assets', []):
                    if asset.get('unrealized_pnl', 0) != 0:
                        pnl = asset['unrealized_pnl']
                        emoji = "📈" if pnl > 0 else "📉"
                        message += f"\n{emoji} Unrealized PnL: `${pnl:.2f}`"
            else:
                message = f"💰 *Spot Account Balance*\n\nTotal: `${balance_info['total']:.2f}`\n"
                
                assets = balance_info.get('assets', [])
                if assets:
                    message += "\n*Assets:*\n"
                    sorted_assets = sorted(assets, key=lambda x: x['usd_value'], reverse=True)
                    
                    for asset in sorted_assets[:10]:  # Show top 10
                        asset_name = asset['asset']
                        total_amount = asset['free'] + asset['locked']
                        usd_value = asset['usd_value']
                        
                        if asset_name == 'USDT':
                            message += f"• {asset_name}: `${total_amount:.2f}`\n"
                        else:
                            message += f"• {asset_name}: `{total_amount:.4f}` (`${usd_value:.2f}`)\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Balance info not available", parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if self.bot_instance:
            status = "🟢 Running" if self.bot_instance.running else "🔴 Stopped"
            message = f"""
📊 *Bot Status*

Status: {status}
Mode: `{Settings.TRADING_MODE}`
Type: `{Settings.TRADING_TYPE}`
"""
            if Settings.TRADING_TYPE == 'futures':
                message += f"Leverage: `{Settings.LEVERAGE}x`\n"
            
            message += f"Risk per trade: `{Settings.RISK_PERCENT}%`\n"
            message += f"Symbol: `{Settings.SYMBOL}`\n"
            message += f"Max daily trades: `{Settings.MAX_DAILY_TRADES}`"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Status info not available", parse_mode='Markdown')
    
    def start(self):
        """Start the telegram bot"""
        if not self.enabled:
            print("Telegram commands not enabled (missing config)")
            return
        
        def run_bot():
            """Run bot in asyncio loop"""
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create application with minimal settings for threading
                builder = Application.builder().token(self.token)
                
                # Disable some features that don't work well in threads
                self.application = builder.build()
                
                # Add handlers
                self.application.add_handler(CommandHandler("start", self.start_command))
                self.application.add_handler(CommandHandler("balance", self.balance_command))
                self.application.add_handler(CommandHandler("status", self.status_command))
                self.application.add_handler(CallbackQueryHandler(self.button_handler))
                
                # Start bot with polling
                print("Starting Telegram command handler...")
                loop.run_until_complete(self.application.initialize())
                loop.run_until_complete(self.application.start())
                loop.run_until_complete(self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES))
                
                # Keep running
                while self.running:
                    time.sleep(1)
                
                # Cleanup
                loop.run_until_complete(self.application.updater.stop())
                loop.run_until_complete(self.application.stop())
                loop.run_until_complete(self.application.shutdown())
                
            except Exception as e:
                print(f"Error in telegram command handler: {e}")
                import traceback
                traceback.print_exc()
            finally:
                loop.close()
        
        # Start in separate thread
        self.running = True
        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
    
    def stop(self):
        """Stop the telegram bot"""
        self.running = False
        if self.application:
            self.application.stop()
