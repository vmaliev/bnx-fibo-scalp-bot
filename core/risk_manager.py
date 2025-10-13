import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
from core.bingx_client import BingXClient
from config.settings import Settings

class RiskManager:
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or Settings.BINGX_API_KEY
        self.secret_key = secret_key or Settings.BINGX_SECRET_KEY
        demo = Settings.TRADING_MODE == 'testnet'
        trading_type = Settings.TRADING_TYPE
        leverage = Settings.LEVERAGE if hasattr(Settings, 'LEVERAGE') else 5
        self.client = BingXClient(self.api_key, self.secret_key, demo=demo, trading_type=trading_type, leverage=leverage)
        self.leverage = leverage
        self.trading_type = trading_type
        
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        self.active_positions = {}
        self.trailing_stops = {}
    
    def reset_daily_counters(self):
        """Reset daily trade counters"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = today
    
    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed based on daily limits"""
        self.reset_daily_counters()
        
        if self.daily_trades >= Settings.MAX_DAILY_TRADES:
            return False, f"Max daily trades reached ({Settings.MAX_DAILY_TRADES})"
        
        if self.daily_pnl < 0:
            loss_pct = abs(self.daily_pnl / self.get_account_balance() * 100)
            if loss_pct >= Settings.MAX_DAILY_LOSS_PERCENT:
                return False, f"Max daily loss reached ({Settings.MAX_DAILY_LOSS_PERCENT}%)"
        
        return True, "Trading allowed"
    
    def get_account_balance(self) -> float:
        """Get account balance (available/free only for backward compatibility)"""
        balance_info = self.get_account_balance_full()
        return balance_info['available']
    
    def get_account_balance_full(self) -> dict:
        """
        Get full account balance info - calculates total assets value in USDT
        For futures: returns available margin and equity
        For spot: calculates total assets value in USDT
        
        Returns:
            dict: {
                'available': float, 
                'locked': float, 
                'total': float,
                'assets': list of {'asset': str, 'free': float, 'locked': float, 'usd_value': float}
            }
        """
        try:
            account = self.client.get_balance()
            print(f"DEBUG get_balance: {account}")
            
            # Handle futures balance differently
            if self.trading_type == 'futures':
                if isinstance(account, dict):
                    # Futures balance structure: {balance: {...}}
                    balance_data = account.get('balance', account)
                    
                    # Extract available margin and equity
                    available_margin = float(balance_data.get('availableMargin', balance_data.get('balance', 0)))
                    equity = float(balance_data.get('equity', balance_data.get('balance', 0)))
                    used_margin = float(balance_data.get('usedMargin', 0))
                    unrealized_pnl = float(balance_data.get('unrealizedProfit', 0))
                    
                    print(f"DEBUG: Futures balance - Available Margin: ${available_margin:.2f}, Equity: ${equity:.2f}, Used: ${used_margin:.2f}")
                    
                    # For futures, show single USDT asset
                    assets = [{
                        'asset': 'USDT',
                        'free': available_margin,
                        'locked': used_margin,
                        'usd_value': equity,
                        'unrealized_pnl': unrealized_pnl
                    }]
                    
                    return {
                        'available': available_margin, 
                        'locked': used_margin, 
                        'total': equity,
                        'assets': assets
                    }
                
                print(f"DEBUG: Could not parse futures balance, returning 0")
                return {'available': 0.0, 'locked': 0.0, 'total': 0.0, 'assets': []}
            
            # Spot balance handling
            total_available_usdt = 0.0
            total_locked_usdt = 0.0
            assets_list = []
            
            if isinstance(account, dict):
                # Try 'balances' (with s) first - BingX spot API format
                balance = account.get('balances', account.get('balance', account.get('data', {})))
                
                if isinstance(balance, list) and len(balance) > 0:
                    # Calculate total assets value in USDT
                    for item in balance:
                        asset = item.get('asset', item.get('coin', ''))
                        free = float(item.get('free', 0))
                        locked = float(item.get('locked', 0))
                        
                        if free == 0 and locked == 0:
                            continue
                        
                        # Convert to USDT value
                        if asset == 'USDT':
                            free_usdt = free
                            locked_usdt = locked
                            current_price = 1.0
                        else:
                            # Get current price for this asset
                            try:
                                symbol = f"{asset}-USDT"
                                klines = self.client.get_klines(symbol, '1m', limit=1)
                                if klines and len(klines) > 0:
                                    # Get close price from last candle
                                    if isinstance(klines[0], dict):
                                        current_price = float(klines[0].get('close', 0))
                                    elif isinstance(klines[0], list) and len(klines[0]) > 4:
                                        current_price = float(klines[0][4])  # Close price
                                    else:
                                        current_price = 0
                                    
                                    free_usdt = free * current_price
                                    locked_usdt = locked * current_price
                                    print(f"DEBUG: {asset} - Free: {free}, Locked: {locked}, Price: ${current_price:.2f}, USDT Value: ${free_usdt + locked_usdt:.2f}")
                                else:
                                    free_usdt = 0
                                    locked_usdt = 0
                                    current_price = 0
                            except Exception as e:
                                print(f"Could not get price for {asset}: {e}")
                                free_usdt = 0
                                locked_usdt = 0
                                current_price = 0
                        
                        # Add to assets list
                        usd_value = free_usdt + locked_usdt
                        if usd_value > 0:  # Only add assets with value
                            assets_list.append({
                                'asset': asset,
                                'free': free,
                                'locked': locked,
                                'usd_value': usd_value,
                                'price': current_price
                            })
                        
                        total_available_usdt += free_usdt
                        total_locked_usdt += locked_usdt
                    
                    total_usdt = total_available_usdt + total_locked_usdt
                    print(f"DEBUG: Total Assets - Available: ${total_available_usdt:.2f}, Locked: ${total_locked_usdt:.2f}, Total: ${total_usdt:.2f}")
                    return {
                        'available': total_available_usdt, 
                        'locked': total_locked_usdt, 
                        'total': total_usdt,
                        'assets': assets_list
                    }
                    
                elif isinstance(balance, dict):
                    # Direct balance field (fallback)
                    free = float(balance.get('free', balance.get('balance', balance.get('available', 0))))
                    locked = float(balance.get('locked', 0))
                    total = free + locked
                    print(f"DEBUG: Parsed balance (dict) - Available: {free}, Locked: {locked}, Total: {total}")
                    assets = [{'asset': 'USDT', 'free': free, 'locked': locked, 'usd_value': total, 'price': 1.0}] if total > 0 else []
                    return {'available': free, 'locked': locked, 'total': total, 'assets': assets}
                    
            print(f"DEBUG: Could not parse balance, returning 0")
            return {'available': 0.0, 'locked': 0.0, 'total': 0.0, 'assets': []}
        except Exception as e:
            print(f"Error getting balance: {e}")
            import traceback
            traceback.print_exc()
            return {'available': 0.0, 'locked': 0.0, 'total': 0.0}
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, balance: float = None) -> float:
        """
        Calculate position size based on risk percentage
        For futures: accounts for leverage to determine contract size
        For spot: uses balance directly
        """
        if balance is None:
            balance = self.get_account_balance()
        
        print(f"DEBUG: Balance={balance}, Entry={entry_price}, Stop={stop_loss}, Trading={self.trading_type}, Leverage={self.leverage if self.trading_type == 'futures' else 'N/A'}")
        
        if balance == 0:
            print("DEBUG: Balance is 0, returning 0")
            return 0.0
        
        # Calculate risk amount (10% of balance)
        risk_amount = balance * (Settings.RISK_PERCENT / 100)
        
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            print("DEBUG: Price risk is 0, returning 0")
            return 0.0
        
        # Calculate position size based on risk
        position_size = risk_amount / price_risk
        print(f"DEBUG: Risk-based position_size={position_size} ({position_size * entry_price:.2f} USD)")
        
        # For futures, we can use leverage to increase position size
        if self.trading_type == 'futures':
            # Max position based on margin and leverage
            # With 5x leverage, we can control 5x our margin
            max_position_value = balance * self.leverage * 0.90  # 90% of max leverage capacity
            max_position_by_balance = max_position_value / entry_price
            print(f"DEBUG: Futures - Max position with {self.leverage}x leverage={max_position_by_balance} ({max_position_value:.2f} USD)")
        else:
            # For spot, cap at 90% of balance
            max_position_by_balance = (balance * 0.90) / entry_price
            print(f"DEBUG: Spot - Max position by balance (90%)={max_position_by_balance} ({max_position_by_balance * entry_price:.2f} USD)")
        
        # ULTRA-AGGRESSIVE: Enforce minimum $1 position
        min_position_value = 1.0  # $1 minimum
        min_position_size = min_position_value / entry_price
        print(f"DEBUG: Minimum position_size={min_position_size} ({min_position_value} USD)")
        
        # Use risk-based size, capped at max leverage capacity, minimum $1
        position_size = min(position_size, max_position_by_balance)
        if position_size < min_position_size:
            print(f"Position too small ({position_size * entry_price:.2f} USD), using minimum ${min_position_value}")
            position_size = min_position_size
        
        print(f"DEBUG: Final position_size={position_size} ({position_size * entry_price:.2f} USD)")
        return position_size
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """Place market order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side.upper(),
                order_type='MARKET',  # Changed from type= to order_type=
                quantity=quantity
            )
            print(f"DEBUG: Order placed successfully: {order}")
            return order
        except Exception as e:
            print(f"Error placing market order: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Optional[Dict]:
        """Place limit order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side.upper(),
                order_type='LIMIT',  # Fixed parameter name
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
            return order
        except Exception as e:
            print(f"Error placing limit order: {e}")
            return None
    
    def place_stop_loss(self, symbol: str, side: str, quantity: float, stop_price: float) -> Optional[Dict]:
        """Place stop-loss order"""
        try:
            stop_side = 'SELL' if side == 'BUY' else 'BUY'
            order = self.client.create_order(
                symbol=symbol,
                side=stop_side,
                order_type='STOP_MARKET',  # Fixed parameter name
                quantity=quantity,
                stopPrice=stop_price
            )
            return order
        except Exception as e:
            print(f"Error placing stop-loss: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def place_take_profit(self, symbol: str, side: str, quantity: float, tp_price: float) -> Optional[Dict]:
        """Place take-profit order"""
        try:
            tp_side = 'SELL' if side == 'BUY' else 'BUY'
            order = self.client.create_order(
                symbol=symbol,
                side=tp_side,
                order_type='TAKE_PROFIT_MARKET',  # Fixed parameter name
                quantity=quantity,
                stopPrice=tp_price
            )
            return order
        except Exception as e:
            print(f"Error placing take-profit: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def execute_trade(self, signal: Dict, symbol: str) -> Optional[Dict]:
        """Execute full trade with entry, stop-loss, and take-profits"""
        can_trade, reason = self.can_trade()
        if not can_trade:
            print(f"Cannot trade: {reason}")
            return None
        
        # Set leverage for futures trading
        if self.trading_type == 'futures':
            print(f"Setting {self.leverage}x leverage for {symbol}...")
            self.client.set_leverage(symbol, self.leverage, 'LONG')
            self.client.set_leverage(symbol, self.leverage, 'SHORT')
        
        balance = self.get_account_balance()
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        direction = signal['direction']
        
        position_size = self.calculate_position_size(entry_price, stop_loss, balance)
        
        # ULTRA-AGGRESSIVE: Removed zero check, minimum $1 enforced in calculate_position_size
        # if position_size == 0:
        #     print("Position size is 0")
        #     return None
        
        if position_size <= 0:
            print(f"ERROR: Position size is {position_size}, should never be zero with $1 minimum!")
            return None
        
        side = 'BUY' if direction == 'up' else 'SELL'
        
        entry_order = self.place_market_order(symbol, side, position_size)
        if not entry_order:
            return None
        
        self.place_stop_loss(symbol, side, position_size, stop_loss)
        
        take_profits = signal['take_profits']
        tp1_qty = position_size * (Settings.TP1_PERCENT / 100)
        tp2_qty = position_size * (Settings.TP2_PERCENT / 100)
        tp3_qty = position_size * (Settings.TP3_PERCENT / 100)
        
        self.place_take_profit(symbol, side, tp1_qty, take_profits['tp1'])
        self.place_take_profit(symbol, side, tp2_qty, take_profits['tp2'])
        self.place_take_profit(symbol, side, tp3_qty, take_profits['tp3'])
        
        self.daily_trades += 1
        
        trade_info = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_size': position_size,
            'take_profits': take_profits,
            'entry_order': entry_order,
            'signal': signal
        }
        
        self.active_positions[symbol] = trade_info
        
        return trade_info
    
    def partial_exit(self, symbol: str, exit_price: float, percentage: float) -> bool:
        """Execute partial exit"""
        if symbol not in self.active_positions:
            return False
        
        position = self.active_positions[symbol]
        remaining_qty = position['position_size']
        exit_qty = remaining_qty * (percentage / 100)
        
        side = 'SELL' if position['direction'] == 'up' else 'BUY'
        order = self.place_market_order(symbol, side, exit_qty)
        
        if order:
            position['position_size'] -= exit_qty
            
            pnl = self._calculate_pnl(position['entry_price'], exit_price, exit_qty, position['direction'])
            self.daily_pnl += pnl
            
            return True
        
        return False
    
    def _calculate_pnl(self, entry_price: float, exit_price: float, quantity: float, direction: str) -> float:
        """Calculate PnL for a trade"""
        if direction == 'up':
            return (exit_price - entry_price) * quantity
        else:
            return (entry_price - exit_price) * quantity
    
    def update_trailing_stop(self, symbol: str, current_price: float):
        """Update trailing stop after first target is hit"""
        if symbol not in self.active_positions:
            return
        
        position = self.active_positions[symbol]
        direction = position['direction']
        entry_price = position['entry_price']
        
        if symbol not in self.trailing_stops:
            if direction == 'up' and current_price >= position['take_profits']['tp1']:
                self.trailing_stops[symbol] = entry_price
            elif direction == 'down' and current_price <= position['take_profits']['tp1']:
                self.trailing_stops[symbol] = entry_price
        else:
            if direction == 'up':
                new_stop = current_price * 0.995
                if new_stop > self.trailing_stops[symbol]:
                    self.trailing_stops[symbol] = new_stop
            else:
                new_stop = current_price * 1.005
                if new_stop < self.trailing_stops[symbol]:
                    self.trailing_stops[symbol] = new_stop
    
    def close_position(self, symbol: str, reason: str = "Manual close") -> bool:
        """Close entire position"""
        if symbol not in self.active_positions:
            return False
        
        position = self.active_positions[symbol]
        side = 'SELL' if position['direction'] == 'up' else 'BUY'
        
        order = self.place_market_order(symbol, side, position['position_size'])
        
        if order:
            del self.active_positions[symbol]
            if symbol in self.trailing_stops:
                del self.trailing_stops[symbol]
            
            print(f"Position closed: {symbol} - {reason}")
            return True
        
        return False
