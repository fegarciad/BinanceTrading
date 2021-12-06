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
    return series.ewm(span=window, adjust=False).mean()


def macd(series: pd.DataFrame, period_long: int = 26, period_short: int = 12, period_signal: int = 9) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return tuple of pandas series with the moving average convergence/divergence and signal line."""
    long_ema = ema(series, window=period_long)
    short_ema = ema(series, window=period_short)

    macd_line = short_ema - long_ema
    signal = ema(macd_line, window=period_signal)

    return macd_line, signal


def rsi(series: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Return Relative Strength Index for a pandas series."""
    delta = series.diff(1)
    delta = delta.dropna()

    d_up, d_down = delta.copy(), delta.copy()
    d_up[d_up < 0] = 0
    d_down[d_down > 0] = 0

    rol_up = d_up.rolling(window).mean()
    rol_down = np.abs(d_down.rolling(window).mean())

    rel_strength = rol_up / rol_down
    return 100 - 100 / (1 + rel_strength)
