########################
# Financial Indicators #
########################

import numpy as np
import pandas as pd


def sma(series: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Return the simple moving average for given series."""
    return series.rolling(window).mean()

def ema(series: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Return the exponencial moving average for given series."""
    return series.ewm(span=window,adjust=False).mean()

def macd(series: pd.DataFrame, period_long: int = 26, period_short: int = 12, period_signal: int = 9)-> tuple[pd.DataFrame,pd.DataFrame]:
    """Return tuple of pandas series with the moving average convergence/divergence and signal line."""
    long_ema = ema(series,window=period_long)
    short_ema = ema(series,window=period_short)

    macd = short_ema - long_ema
    signal = ema(macd,window=period_signal)

    return macd, signal

def rsi(series: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Return Relative Strength Index for a pandas series."""
    delta = series.diff(1)
    delta = delta.dropna()
    
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0

    RolUp = dUp.rolling(window).mean()
    RolDown = np.abs(dDown.rolling(window).mean())

    RS = RolUp / RolDown
    return 100 - 100 / (1 + RS)