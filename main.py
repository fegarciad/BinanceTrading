###############################
# Main Binance Trading Script #
###############################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

from config import API_KEY, API_SECRET

from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot


# Main function 
def main(symbol,order_size,interval,duration,lookback,paper_trade):
    exchange = Exchange(API_KEY,API_SECRET)
    print(exchange.account_balance(),'\n')

    strategy = RandomStrategy()
    # strategy = MACDStrategy()
    tradebot = TradingBot(exchange,strategy,symbol,order_size,interval,duration,lookback,paper_trade)
    tradebot.run()


if __name__ == '__main__':
    main('BTCUSDT',0.0005,'1m',duration=int(10*60),lookback=5,paper_trade=True)

