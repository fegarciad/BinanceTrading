######################################
# Example Historic Candle Stick Data #
######################################

from binancetrading import Exchange

COIN = 'BTC'
INTERVAL = '1m'
LOOKBACK = 10

exchange = Exchange()
data = exchange.kline_df(COIN, INTERVAL, LOOKBACK)

print(data)
