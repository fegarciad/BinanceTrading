##########################
## Binance trading script
##########################

"""
IF USING WEBSOCKETS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os
import time
from datetime import datetime

import pandas as pd
import numpy as np
from binance.spot import Spot
from binance.websocket.spot.websocket_client import \
    SpotWebsocketClient as WebsocketClient

from config import API_KEY, API_SECRET

########################
# Financial Indicators #
########################

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

####################################
# Handle Kline data from WebSocket #
####################################

def refreshCandles(candle,candleList,maxLen=500):
    """
    Recieve candlestick data and append to candlestick list
    if it is new candlestick.
    candle: Candlestick dictionary
    candleList: List of candlesticks
    maxLen: Maximum length of list. As new candlesticks enter,
    it removes old candlesticks.
    """
    changed = False
    if candle['k']['x'] == True:
        if candleList:
            if candle['k']['t'] != candleList[-1]['t']:
                candleList.append(candle['k'])
                changed = True
                if len(candleList) > maxLen:
                    candleList.pop(0)
        else:
            candleList.append(candle['k'])
            changed = True
    return candleList, changed

def candleToDF(candleList):
    """
    Convert list of candlesticks to DataFrame
    """
    headers = ['Start Time','Close Time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
    candleDF = pd.DataFrame(candleList,index=[i for i in range(len(candleList))])
    candleDF.set_axis(headers, axis=1, inplace=True)
    candleDF['Start Time'] = pd.to_datetime(candleDF['Start Time'], unit='ms')
    candleDF['Close Time'] = pd.to_datetime(candleDF['Close Time'], unit='ms')
    return candleDF[['Start Time','Close Time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?']]

candleList = []
def WS_message_handler(msg):
    global candleList
    try:
        candleList, changed = refreshCandles(msg,candleList,maxLen=3)
        if changed:
            candleDF = candleToDF(candleList)
            print(candleDF)
    except:
        print(msg)


def main(client,runningTime=120):

    # Get account information
    # print(client.account())
    # print(client.exchange_info(symbol='BTCUSDT'))

    # params = {
    #     "symbol": "BTCUSDT",
    #     "side": "BUY",
    #     "type": "MARKET",
    #     # "timeInForce": "GTC",
    #     "quoteOrderQty": 10,
    #     # "price": 9500,
    # }

    # response = client.new_order_test(**params)
    # print(response)
        
    ws_client = WebsocketClient()
    ws_client.start()

    ws_client.kline(
        symbol='btcusdt',
        interval='1m',
        id=1,
        callback=WS_message_handler,
    )

    time.sleep(runningTime)
    ws_client.stop()

    # candles = pd.DataFrame(client.klines('BTCUSDT','1h'))
    # candles = client.klines('BTCUSDT','1h')
    # print(candles)

if __name__ == '__main__':
    client = Spot(key=API_KEY, secret=API_SECRET)
    main(client,runningTime=100)
