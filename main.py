##########################
# Binance trading script #
##########################

"""
IF USING WEBSOCKETS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from binance.spot import Spot
from binance.websocket.spot.websocket_client import \
    SpotWebsocketClient as WebsocketClient

from config import API_KEY, API_SECRET

cd = os.getcwd()+'\\'

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

######################
# Trading Strategies #
######################

# 1. MACD strategy, if MACD line crosses signal line, buy or sell.

def macdStrategy(DF,plot=False,filter=True,name='MACD'):
    """
    Returns dataframe with dates and type of suggested trades. 
    If plot, then plots prices and marks when to buy or sell.
    DF: Dataframe with price and date columns.
    plot: If true, plots price chart and when to buy or sell.
    filter: If true returns only rows of suggested trades.
    """
    Buy = []
    Sell = []
    flag = False

    date_col = 'Close time'
    price_col = 'Close price'

    prices =  DF[[date_col,price_col]].sort_values(by=date_col).reset_index(drop=True)
    MACD, SIG = macd(prices[price_col])
    prices['MACD'] = MACD
    prices['Signal'] = SIG

    for _, row in prices.iterrows():
        if row['MACD'] > row['Signal']:
            Sell.append(np.nan)
            if not flag:
                Buy.append(row[price_col])
                flag = True
            else:
                Buy.append(np.nan)
        elif row['MACD'] < row['Signal']:
            Buy.append(np.nan)
            if flag:
                Sell.append(row[price_col])
                flag = False
            else:
                Sell.append(np.nan)
        else:
            Buy.append(np.nan)
            Sell.append(np.nan)
    
    AuxDF = prices.copy()
    AuxDF['Buy'] = Buy
    AuxDF['Sell'] = Sell

    if plot:
        _, ax = plt.subplots(1,1,figsize=(10,8))
        ax.plot(AuxDF[date_col],AuxDF[price_col],zorder=1)
        ax.plot(AuxDF[date_col],AuxDF['MACD'],zorder=1)
        ax.plot(AuxDF[date_col],AuxDF['Signal'],zorder=1)
        ax.scatter(AuxDF[date_col],AuxDF['Buy'], color='green', label='Buy', marker='^',s=75,zorder=2)
        ax.scatter(AuxDF[date_col],AuxDF['Sell'], color='red', label='Sell', marker='v',s=75,zorder=2)
        ax.set_xlabel('Dates',fontsize=20)
        ax.set_title('{} Strategy'.format(name),fontsize=30,y=1.03)
        ax.legend(fontsize=15)
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.savefig('Images//{} Strategy.png'.format(name))
        plt.show()
    
    if filter:
        AuxDF = AuxDF.dropna(how='all',subset=['Buy','Sell'])

    # AuxDF.rename(columns={date_col:'Date',price_col:'Price'},inplace=True)
    return AuxDF[[date_col,price_col,'Buy','Sell']]

####################################
# Handle Kline data from WebSocket #
####################################

def refreshCandles(candle,candleList,maxLen=500):
    """
    Recieve candlestick data and append to candlestick list
    if it is new candlestick.
    candle: Candlestick dictionary.
    candleList: List of candlesticks.
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

def WScandleToDF(candleList):
    """
    Convert list of candlesticks from WebSocket to DataFrame.
    """
    headers = ['Open time','Close time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
    candleDF = pd.DataFrame(candleList,index=[i for i in range(len(candleList))])
    candleDF.set_axis(headers, axis=1, inplace=True)
    candleDF['Open time'] = pd.to_datetime(candleDF['Open time'], unit='ms')
    candleDF['Close time'] = pd.to_datetime(candleDF['Close time'], unit='ms')
    return candleDF[['Open time','Close time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?']]

def candleToDF(candledata,symbol,interval):
    """
    Convert candlesticks historic table to DataFrame.
    """
    headers = ['Open time','Open price','High price','Low price','Close price','Base asset volume','Close time','Quote asset volume','Number of trades','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
    candleDF = pd.DataFrame(candledata)
    candleDF.set_axis(headers, axis=1, inplace=True)
    candleDF['Open time'] = pd.to_datetime(candleDF['Open time'], unit='ms')
    candleDF['Close time'] = pd.to_datetime(candleDF['Close time'], unit='ms')
    candleDF['Symbol'] = symbol
    candleDF['Interval'] = interval
    candleDF['Kline closed?'] = True
    return candleDF[['Open time','Close time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?']]

def candleToList(candledata,symbol,interval):
    """
    Convert candlesticks historic table to candlestick list of dictionaries.
    """
    candleList = []
    for candle in candledata:
        candleDict = {'k':{
            "t": candle[0],  # Kline start time
            "T": candle[6],  # Kline close time
            "s": symbol,     # Symbol
            "i": interval,   # Interval
            "f": 0,          # First trade ID
            "L": 0,          # Last trade ID
            "o": candle[1],  # Open price
            "c": candle[4],  # Close price
            "h": candle[2],  # High price
            "l": candle[3],  # Low price
            "v": candle[5],  # Base asset volume
            "n": candle[8],  # Number of trades
            "x": True,       # Is this kline closed?
            "q": candle[7],  # Quote asset volume
            "V": candle[9],  # Taker buy base asset volume
            "Q": candle[10], # Taker buy quote asset volume
            "B": candle[11]  # Ignore
            }}
        candleList.append(candleDict['k'])
    return candleList

def WS_message_handler(msg):
    """
    Recieve WebSocket data, refresh candlestick DataFrame, evaluate trade strategy 
    and eventually execute trades.
    """
    global candleList
    try:
        candleList, changed = refreshCandles(msg,candleList,maxLen=8)
        if changed:
            candleDF = WScandleToDF(candleList)
            print(candleDF)
            # Write to log file
            with open(cd+'CandleSticks.txt','w') as f:
                dfAsString = candleDF.to_string(header=True, index=False)
                f.write(dfAsString)
    except Exception as err:
        print(msg,err)

#################
# Main Function #
#################

def main(client,runningTime=120):
    global candleList

    symbol = 'BTCUSDT'
    interval = '1m'
    
    candleList = candleToList(client.klines(symbol,interval,limit=5),symbol,interval)
        
    ws_client = WebsocketClient()
    ws_client.start()

    ws_client.kline(
        symbol=symbol,
        interval=interval,
        id=1,
        callback=WS_message_handler,
    )

    time.sleep(runningTime)
    ws_client.stop()

if __name__ == '__main__':
    client = Spot(key=API_KEY, secret=API_SECRET)
    candleList = []
    main(client,runningTime=300)
    