######################
# Example Live Chart #
######################

import binancetrading as bt

APIURL = 'https://api.binance.com'
WSURL = 'wss://stream.binance.com:9443/ws'

COIN = 'BTC'
INTERVAL = '1m'

exchange = bt.Exchange(wsurl=WSURL)
exchange.live_chart(COIN, INTERVAL)
