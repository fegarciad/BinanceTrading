##########################
## Binance trading script
##########################

"""
IF USING WEBSOCKETS RUN FOLLOWING CODE IN CMD BEFORE SCRIPT
--> pip install certifi
--> for /f %i in ('python -m certifi') do set SSL_CERT_FILE=%i
"""

import os
import time
from datetime import datetime

import pandas as pd
from binance.spot import Spot
from binance.websocket.spot.websocket_client import \
    SpotWebsocketClient as WebsocketClient

from config import API_KEY, API_SECRET


def main(client):

    # Get account information
    print(client.account())

    # Post a new order
    params = {
        'symbol': 'BTCUSDT',
        'side': 'SELL',
        'type': 'MARKET',
        # 'timeInForce': 'GTC',
        'quantity': 0.001,
        # 'price': 50000
    }

    response = client.new_order_test(**params)
    print(response)

    def message_handler(message):
        print(message)

    ws_client = WebsocketClient()
    ws_client.start()

    ws_client.agg_trade(
        symbol='btcusdt',
        id=1,
        callback=message_handler,
    )

    time.sleep(5)

    ws_client.stop()

    candles = pd.DataFrame(client.klines('BTCUSDT','1h'))
    candles = client.klines('BTCUSDT','1h')

    print(candles)

if __name__ == '__main__':
    client = Spot(key=API_KEY, secret=API_SECRET)
    main(client)
