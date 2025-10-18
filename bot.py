#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import signal
import sys
from datetime import datetime
from core.data_fetcher import DataFetcher
from core.strategy import FiboScalpStrategy
from core.risk_manager import RiskManager
from core.logger import TradeLogger
from core.telegram_notifier import TelegramNotifier
from core.telegram_commands import TelegramCommandHandler
from config.settings import Settings

class FiboScalpBot:
    def __init__(self):
        self.logger = TradeLogger()
        self.notifier = TelegramNotifier()
        self.data_fetcher = DataFetcher()
        self.strategy = FiboScalpStrategy(self.data_fetcher)
        self.risk_manager = RiskManager()
        
        # Initialize telegram command handler
        self.command_handler = TelegramCommandHandler()
        self.command_handler.set_bot_instance(self)
        self.command_handler.set_balance_callback(lambda: self.risk_manager.get_account_balance_full())
        
        self.running = False
        self.symbol = Settings.SYMBOL
        self.timeframes = Settings.TIMEFRAMES
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutting down bot...")
        self.running = False
        self.command_handler.stop()
        sys.exit(0)
    
    def start(self):
        """Start the bot"""
        self.running = True
        
        # Start telegram command handler
        self.command_handler.start()
        
        self.logger.info("Starting Fibo Scalp Bot - Mode: {}".format(Settings.TRADING_MODE))
        self.logger.info("Trading Type: {}".format(Settings.TRADING_TYPE))
        if Settings.TRADING_TYPE == 'futures':
            self.logger.info("Leverage: {}x".format(Settings.LEVERAGE))
        self.logger.info("Risk per trade: {}%".format(Settings.RISK_PERCENT))
        self.logger.info("Symbol: {}".format(self.symbol))
        self.logger.info("Timeframes: {}".format(', '.join(self.timeframes)))
        
        # Get initial balance
        balance_info = self.risk_manager.get_account_balance_full()
        balance_text = self.notifier._format_balance_info(balance_info)
        
        trading_info = "Mode: {}\nType: {}".format(Settings.TRADING_MODE, Settings.TRADING_TYPE)
        if Settings.TRADING_TYPE == 'futures':
            trading_info += "\nLeverage: {}x\nRisk: {}%".format(Settings.LEVERAGE, Settings.RISK_PERCENT)
        
        self.notifier.send_sync("*Bot Started*\n\n{}\nSymbol: {}{}".format(trading_info, self.symbol, balance_text))
        
        self.run_loop()
    
    def run_loop(self):
        """Main trading loop"""
        iteration = 0
        while self.running:
            try:
                iteration += 1
                self.logger.info("=== Iteration {} - Checking market ===".format(iteration))
                
                market_data = self.data_fetcher.get_market_data(self.symbol, self.timeframes)
                
                if not market_data:
                    self.logger.warning("No market data available")
                    time.sleep(60)
                    continue
                
                self.logger.info("Market data fetched: {} timeframes".format(len(market_data)))
                
                # Log current price
                df_1m = market_data.get('1m')
                if df_1m is not None and not df_1m.empty:
                    current_price = df_1m['close'].iloc[-1]
                    self.logger.info("Current {} price: ${:,.2f}".format(self.symbol, current_price))
                
                signal = self.strategy.generate_signal(market_data)
                
                if signal:
                    self.logger.info("SIGNAL FOUND: {} on {}".format(signal['direction'], signal['timeframe']))
                    self.logger.info("   Entry: ${:.2f}, Stop: ${:.2f}".format(signal['entry_price'], signal['stop_loss']))
                    
                    trade_info = self.risk_manager.execute_trade(signal, self.symbol)
                    
                    if trade_info:
                        self.logger.info("Trade executed: {}".format(trade_info))
                        
                        self.logger.log_trade({
                            'timestamp': trade_info['timestamp'],
                            'symbol': self.symbol,
                            'direction': trade_info['direction'],
                            'action': 'ENTRY',
                            'entry_price': trade_info['entry_price'],
                            'exit_price': 0,
                            'quantity': trade_info['position_size'],
                            'stop_loss': trade_info['stop_loss'],
                            'pnl': 0,
                            'reason': signal['reason']
                        })
                        
                        # Get current balance and notify
                        balance_info = self.risk_manager.get_account_balance_full()
                        self.notifier.notify_entry(trade_info, balance_info=balance_info)
                    else:
                        self.logger.warning("❌ Trade execution failed (check balance/minimums)")
                else:
                    self.logger.info("No signal - waiting for setup...")
                
                self.monitor_positions(market_data)
                
                self.logger.info("Sleeping 60 seconds until next check...")
                time.sleep(60)
                
            except Exception as e:
                self.logger.error("Error in main loop: {}".format(e))
                self.notifier.notify_error("Main loop error: {}".format(str(e)))
                time.sleep(60)
    
    def monitor_positions(self, market_data):
        """Monitor and manage active positions"""
        if not self.risk_manager.active_positions:
            return
        
        for symbol in list(self.risk_manager.active_positions.keys()):
            position = self.risk_manager.active_positions[symbol]
            
            df_1m = market_data.get('1m')
            if df_1m is None or df_1m.empty:
                continue
            
            current_price = df_1m['close'].iloc[-1]
            
            self.risk_manager.update_trailing_stop(symbol, current_price)
            
            if symbol in self.risk_manager.trailing_stops:
                trailing_stop = self.risk_manager.trailing_stops[symbol]
                
                if position['direction'] == 'up' and current_price <= trailing_stop:
                    self.logger.info("Trailing stop hit for {}".format(symbol))
                    self.risk_manager.close_position(symbol, "Trailing stop")
                    balance_info = self.risk_manager.get_account_balance_full()
                    self.notifier.notify_stop_loss(symbol, current_price, 0, balance_info=balance_info)
                
                elif position['direction'] == 'down' and current_price >= trailing_stop:
                    self.logger.info("Trailing stop hit for {}".format(symbol))
                    self.risk_manager.close_position(symbol, "Trailing stop")
                    balance_info = self.risk_manager.get_account_balance_full()
                    self.notifier.notify_stop_loss(symbol, current_price, 0, balance_info=balance_info)

def main():
    bot = FiboScalpBot()
    bot.start()

if __name__ == '__main__':
    main()
