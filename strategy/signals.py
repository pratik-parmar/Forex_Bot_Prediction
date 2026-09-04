import pandas as pd
from strategy.indicators import calculate_rsi, calculate_sma, calculate_macd
from strategy.risk_manager import evaluate_risk

def generate_prediction_signal(df: pd.DataFrame, symbol: str = "EURUSD"):
    """
    Analyzes technical indicators to generate Forex trading prediction signals.
    """
    if df is None or df.empty or len(df) < 26:
        return {
            "symbol": symbol,
            "signal": "HOLD",
            "reason": "Insufficient market data for indicator calculation",
            "rsi": None,
            "sma_20": None,
            "sma_50": None
        }

    # Calculate indicators
    df['SMA_20'] = calculate_sma(df['close'], period=20)
    df['SMA_50'] = calculate_sma(df['close'], period=50)
    df['RSI'] = calculate_rsi(df['close'], period=14)
    macd_line, signal_line = calculate_macd(df['close'])
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    rsi_val = float(latest['RSI'])
    sma20 = float(latest['SMA_20'])
    sma50 = float(latest['SMA_50'])
    close_price = float(latest['close'])

    signal = "HOLD"
    reason = "No clear convergence or indicator crossover detected."

    # Signal Generation Logic
    if rsi_val < 30 and sma20 > sma50 and close_price > sma20:
        signal = "BUY"
        reason = "Oversold conditions met (RSI < 30) with bullish SMA crossover trend."
    elif rsi_val > 70 and sma20 < sma50 and close_price < sma20:
        signal = "SELL"
        reason = "Overbought conditions met (RSI > 70) with bearish SMA crossover trend."

    # Risk Management Evaluation
    risk_assessment = evaluate_risk(signal=signal, close_price=close_price)

    return {
        "symbol": symbol,
        "signal": signal,
        "price": close_price,
        "rsi": round(rsi_val, 2),
        "sma_20": round(sma20, 4),
        "sma_50": round(sma50, 4),
        "reason": reason,
        "risk_management": risk_assessment
    }