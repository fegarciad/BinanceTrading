########################
# Financial Indicators #
########################

import numpy as np


def sma(series,window=30):
    """
    Return the simple moving average for given series.
    series: pandas price series.
    window: rolling average window.
    """
    return series.rolling(window).mean()

def ema(series,window=30):
    """
    Return the exponencial moving average for given series.
    series: pandas price series.
    window: rolling average window.
    """
    return series.ewm(span=window,adjust=False).mean()

def macd(series,period_long=26, period_short=12, period_signal=9):
    """
    Return tuple of pandas series with the moving average convergence/divergence and signal line.
    series: pandas price series.
    period_long: long rolling average window.
    period_short: short rolling average window.
    period_signal: rolling average window for signal line.
    """
    long_ema = ema(series,window=period_long)
    short_ema = ema(series,window=period_short)

    macd = short_ema - long_ema
    signal = ema(macd,window=period_signal)

    return macd, signal

def rsi(series,window=14):
    """
    Return Relative Strength Index for a pandas series.
    series: pandas price series
    window: rolling average window
    """
    delta = series.diff(1)
    delta = delta.dropna()
    
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0

    RolUp = dUp.rolling(window).mean()
    RolDown = np.abs(dDown.rolling(window).mean())

    RS = RolUp / RolDown
    return 100 - 100 / (1 + RS)