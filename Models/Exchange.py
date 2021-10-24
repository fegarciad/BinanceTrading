##############################
# WebSocket Helper Functions #
##############################

import numpy as np
import pandas as pd

import os
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from binance.spot import Spot
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from config import API_KEY, API_SECRET

class Exchange():

    def __init__(self,symbol,WShandler,url=''):
        self.api = API_KEY
        self.secret = API_SECRET
        self.url = url if url else "wss://stream.binance.com:9443"

        self.Client = Spot(key=self.api, secret=self.secret)
        self.WebsocketClient = SpotWebsocketClient(stream_url=url)

        self.Trades = []

    def startWS(self):
        pass

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

def candleListToDF(candleList):
    """
    Convert list of candlesticks from WebSocket to DataFrame.
    """
    headers = ['Open time','Close time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
    candleDF = pd.DataFrame(candleList,index=[i for i in range(len(candleList))])
    candleDF.set_axis(headers, axis=1, inplace=True)
    candleDF['Open time'] = pd.to_datetime(candleDF['Open time'], unit='ms')
    candleDF['Close time'] = pd.to_datetime(candleDF['Close time'], unit='ms')
    candleDF['Close price'] = candleDF['Close price'].astype('float')
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
    return candleDF[['Open time','Close time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume']]

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

# def WS_message_handler(msg):
#     """
#     Recieve WebSocket data, refresh candlestick DataFrame, evaluate trade strategy 
#     and eventually execute trades.
#     """
#     global candleList, tradeList
#     try:
#         candleList, changed = refreshCandles(msg,candleList,maxLen=120)
#         if changed:
#             candleDF = WScandleToDF(candleList)
#             MACD = macdStrategy(candleDF,filter=False)
#             execStrat(MACD)
#             # Write to log file
#             with open(cd+'CandleSticks.txt','w') as f:
#                 dfAsString = MACD.to_string(header=True, index=False)
#                 f.write(dfAsString)
#     except Exception as err:
#         print(msg,err)