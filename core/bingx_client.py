"""
BingX API Client
Using HTTP requests with HMAC signature
"""

import time
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from typing import List, Dict, Optional

class BingXClient:
    """Simple BingX API client using HTTP requests"""
    
    def __init__(self, api_key: str, secret_key: str, demo: bool = False, trading_type: str = 'spot', leverage: int = 5):
        """
        Initialize BingX client with HTTP requests
        
        Args:
            api_key: BingX API key
            secret_key: BingX secret key
            demo: Use demo/testnet mode
            trading_type: 'spot' or 'futures'
            leverage: Futures leverage (1-125)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.trading_type = trading_type.lower()
        self.leverage = leverage
        
        # Set base URL based on mode
        if demo:
            self.base_url = 'https://open-api-vst.bingx.com'
        else:
            self.base_url = 'https://open-api.bingx.com'
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request with proper signature"""
        if params is None:
            params = {}
        
        try:
            # Add timestamp
            params['timestamp'] = int(time.time() * 1000)
            
            # Create query string
            query_string = urlencode(sorted(params.items()))
            
            # Generate signature
            signature = self._generate_signature(query_string)
            
            # Add signature to params
            params['signature'] = signature
            
            # Headers
            headers = {
                'X-BX-APIKEY': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Build full URL
            url = f"{self.base_url}{endpoint}"
            
            # Make request
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, data=params, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            result = response.json()
            print(f"DEBUG API response: {result}")
            return result
            
        except Exception as e:
            print(f"API request error: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Dict]:
        """
        Get kline/candlestick data
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            interval: Time interval ('1m', '5m', '15m', '1h', etc.)
            limit: Number of candles to fetch
            
        Returns:
            List of kline data
        """
        try:
            # Format symbol correctly for API
            # Both spot AND futures klines use hyphen format (BTC-USDT)
            if '-' not in symbol:
                symbol = symbol[:3] + '-' + symbol[3:]  # Convert BTCUSDT to BTC-USDT
            
            formatted_symbol = symbol
            
            params = {
                'symbol': formatted_symbol,
                'interval': interval,
                'limit': limit
            }
            
            # Use different endpoint based on trading type
            if self.trading_type == 'spot':
                endpoint = '/openApi/spot/v1/market/kline'
            else:
                endpoint = '/openApi/swap/v2/quote/klines'
            
            response = self._request('GET', endpoint, params)
            
            if response and 'data' in response:
                data = response['data']
                if data is not None:
                    return data
            
            return []
            
        except Exception as e:
            print(f"Error fetching klines: {e}")
            return []
    
    def set_leverage(self, symbol: str, leverage: int, side: str = 'LONG') -> bool:
        """
        Set leverage for futures trading
        
        Args:
            symbol: Trading pair (e.g., 'BTC-USDT')
            leverage: Leverage value (1-125)
            side: 'LONG' or 'SHORT'
            
        Returns:
            True if successful
        """
        if self.trading_type != 'futures':
            return True  # Not applicable for spot trading
        
        try:
            formatted_symbol = symbol.replace('-', '')
            params = {
                'symbol': formatted_symbol,
                'leverage': leverage,
                'side': side
            }
            endpoint = '/openApi/swap/v2/trade/leverage'
            response = self._request('POST', endpoint, params)
            return response.get('code') == 0 or 'success' in str(response).lower()
        except Exception as e:
            print(f"Error setting leverage: {e}")
            return False
    
    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Account balance info
        """
        try:
            # Use different endpoint based on trading type
            if self.trading_type == 'spot':
                endpoint = '/openApi/spot/v1/account/balance'
            else:
                endpoint = '/openApi/swap/v2/user/balance'
            
            response = self._request('GET', endpoint)
            if response and 'data' in response:
                return response['data']
            return {}
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return {}
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                     quantity: float, price: float = None, **kwargs) -> Optional[Dict]:
        """
        Create an order
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'  
            order_type: 'MARKET', 'LIMIT', etc.
            quantity: Order quantity
            price: Order price (for limit orders)
            
        Returns:
            Order response
        """
        try:
            # CRITICAL: Spot NEEDS hyphen (BTC-USDT), Futures needs NO hyphen (BTCUSDT)
            if self.trading_type == 'spot':
                # Ensure hyphen for spot
                formatted_symbol = symbol if '-' in symbol else f"{symbol[:3]}-{symbol[3:]}"
            else:
                # Remove hyphen for futures
                formatted_symbol = symbol.replace('-', '')
            
            params = {
                'symbol': formatted_symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            
            # Add futures-specific parameters
            if self.trading_type == 'futures':
                # Set position side based on buy/sell
                params['positionSide'] = 'LONG' if side == 'BUY' else 'SHORT'
            
            if price:
                params['price'] = price
            
            params.update(kwargs)
            
            # Use different endpoint based on trading type
            if self.trading_type == 'spot':
                endpoint = '/openApi/spot/v1/trade/order'
            else:
                endpoint = '/openApi/swap/v2/trade/order'
            
            response = self._request('POST', endpoint, params)
            
            if response and 'data' in response:
                return response['data']
            
            return response
            
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol.replace('-', '')
            
            response = self._request('GET', '/openApi/swap/v2/trade/openOrders', params, signed=True)
            
            if response and 'data' in response:
                orders = response['data']
                if isinstance(orders, dict):
                    return orders.get('orders', [])
                elif isinstance(orders, list):
                    return orders
            
            return []
            
        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        try:
            params = {
                'symbol': symbol.replace('-', ''),
                'orderId': order_id
            }
            response = self._request('DELETE', '/openApi/swap/v2/trade/order', params, signed=True)
            return response.get('code') == 0
        except Exception as e:
            print(f"Error canceling order: {e}")
            return False
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get current positions"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol.replace('-', '')
            
            response = self._request('GET', '/openApi/swap/v2/user/positions', params, signed=True)
            
            if response and 'data' in response:
                return response['data']
            
            return []
            
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []
