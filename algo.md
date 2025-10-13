The trading algorithm is a scalping strategy designed for sideways or ranging markets. It avoids strongly trending markets and focuses on capturing small profits from price oscillations within a consolidated range.

### 1. Market Condition Analysis (1H & 15m Timeframes)

The bot first determines the overall market condition using higher timeframes:

*   **Sideways Market Detection**: It checks if the price is close to the 50 and 200-period EMAs and if the EMAs are relatively flat.
*   **Trend Avoidance**: If a strong, clear trend is detected (price far from EMAs, steep EMAs), the bot will not trade.

### 2. Fibo Retracement Setup (5m & 1m Timeframes)

Once a sideways market is confirmed, the bot looks for a setup on lower timeframes:

*   **Impulse Wave Detection**: It identifies a sharp, fast price movement (an "impulse wave").
*   **Swing Point Identification**: It finds the swing high and swing low of that impulse move.
*   **Fibonacci Levels**: It calculates Fibonacci retracement levels, targeting the **0.382-0.618 "golden zone"** for entry.

### 3. Entry Confirmation

When the price pulls back into the target Fibonacci zone, the bot waits for one of the following confirmation signals:

*   **RSI Reversal**: The RSI reverses from an oversold (<30) or overbought (>70) condition.
*   **Candlestick Pattern**: A bullish or bearish reversal candle pattern (e.g., engulfing candle) forms.

### 4. Entry Trigger

The final trigger for entry is a breakout:

*   **Long Trade**: The price must break above a recent short-term high.
*   **Short Trade**: The price must break below a recent short-term low.

### 5. Trade Management

*   **Stop Loss**: A stop loss is automatically set just beyond the **0.786** Fibonacci level.
*   **Take Profit**: A staged exit strategy is used, with partial profits taken at three Fibonacci extension levels (0.236, 0.0, and 1.272).
*   **Trailing Stop**: After the first take-profit target is hit, the stop loss is moved to the breakeven point to protect the trade.
