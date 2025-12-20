import pandas as pd
import pandas_ta as ta # If available, otherwise manual

def calculate_rsi(df, period=14):
    """
    Calculates RSI for the given dataframe.
    Expects 'Close' column.
    Returns dataframe with 'RSI' column.
    """
    if df.empty or 'Close' not in df.columns:
        return df
    
    # Manual RSI calculation if pandas_ta is not guaranteed/wanted
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    ma_up = up.rolling(window=period).mean()
    ma_down = down.rolling(window=period).mean()
    
    # Use exponential moving average for better smoothing (Wilder's smoothing)
    # ma_up = up.ewm(com=period - 1, adjust=True, min_periods=period).mean()
    # ma_down = down.ewm(com=period - 1, adjust=True, min_periods=period).mean()

    # Simple approximation for robustness with small datasets
    rs = ma_up / ma_down
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def calculate_cumulative_flows(df):
    """
    Calculates cumulative sum of Net_Flow.
    Expects 'Net_Flow' column.
    Returns dataframe with 'Cumulative_Flow' column.
    """
    if df.empty or 'Net_Flow' not in df.columns:
        return df
    
    # Sort by date first just in case
    df = df.sort_values("Date", ascending=True)
    df['Cumulative_Flow'] = df['Net_Flow'].cumsum()
    return df
