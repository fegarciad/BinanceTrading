######################
# Example Live Chart #
######################

from binancetrading import Exchange

COIN = 'BTC'
INTERVAL = '1m'

exchange = Exchange()
exchange.live_chart(COIN, INTERVAL)
