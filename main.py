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
from binance.spot import Spot
from binance.websocket.spot.websocket_client import \
    SpotWebsocketClient as WebsocketClient

from config import API_KEY, API_SECRET

candleList = []

def refreshCandles(candle,candleList,maxLen=500):
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
    headers = ['Start Time','Close Time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
    candleDF = pd.DataFrame(candleList,index=[i for i in range(len(candleList))])
    candleDF.set_axis(headers, axis=1, inplace=True)
    candleDF['Start Time'] = pd.to_datetime(candleDF['Start Time'], unit='ms')
    candleDF['Close Time'] = pd.to_datetime(candleDF['Close Time'], unit='ms')
    return candleDF[['Start Time','Close Time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?']]

def message_handler(msg):
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
        callback=message_handler,
    )

    time.sleep(runningTime)
    ws_client.stop()

    candles = pd.DataFrame(client.klines('BTCUSDT','1h'))
    candles = client.klines('BTCUSDT','1h')
    print(candles)

if __name__ == '__main__':
    client = Spot(key=API_KEY, secret=API_SECRET)
    main(client,runningTime=1)
