######################################
# Example Historic Candle Stick Data #
######################################

import binancetrading as bt

APIURL = 'https://api.binance.com'
WSURL = 'wss://stream.binance.com:9443/ws'

COIN = 'BTC'
INTERVAL = '1m'
LOOKBACK = 10

exchange = bt.Exchange(wsurl=WSURL)
data = exchange.kline_df(COIN, INTERVAL, LOOKBACK)

print(data)
