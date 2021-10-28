##################
# Exchange Class #
##################

import time

import matplotlib.pyplot as plt
import pandas as pd

from binance.error import ClientError
from binance.spot import Spot
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from matplotlib.animation import FuncAnimation


class Exchange():

    def __init__(self,api,secret,url='',commission=0.00075):
        self.url = url if url else 'wss://stream.binance.com:9443/ws'
        self.commission = commission

        self.Client = Spot(key=api, secret=secret)
        self.WebsocketClient = SpotWebsocketClient(stream_url=self.url)

        self.symbol = ''
        self.Trades = []
        self.Position = 0
        self.CashPosition = 0
        self.Commissions = 0

    def init_portfolio(self,symbol,paper_trade):
        self.symbol = symbol
        if paper_trade:
            self.Position = 0.1
            self.CashPosition = 1000
        else:
            acc = self.account_balance()
            base_curr = symbol[:-4]
            self.Position = acc[acc.index == base_curr,'free'][base_curr]
            self.CashPosition = acc[acc.index == 'USDT','free']['USDT']

    def account_balance(self):
        acc_df = pd.DataFrame(self.Client.account()['balances'])
        acc_df[['free','locked']] = acc_df[['free','locked']].astype(float)
        acc_df.set_index('asset',inplace=True)
        return acc_df.loc[(acc_df['free'] != 0.0)|(acc_df['free'] != 0.0)]

    def refresh_positions(self,side,price,ammount):
        if side == 'BUY':
            self.Position += ammount
            self.CashPosition -= ammount*price
            self.Commissions += ammount*price*self.commission
        if side == 'Sell':
            self.Position -= ammount
            self.CashPosition += ammount*price
            self.Commissions += ammount*price*self.commission

    def make_market_order(self,symbol,side,ammount):
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": ammount,
            }
        try:
            order = self.Client.new_order(**params)
            t = time.strftime('%Y-%m-%d %H:%M', time.localtime(order['transactTime']/1000))
            price = float(order['cummulativeQuoteQty'])/float(order['executedQty'])
            op = {'Symbol':symbol, 'Side':side, 'Price':price, 'Ammount':ammount, 'Time':t}
            self.Trades.append(op)
            self.refresh_positions(side,price,ammount)
            print('Order: {} {} {} for ${:,.2f} (${:,.2f} total) at {}\n'.format(side,ammount,symbol,price,price*ammount,t))
        except ClientError as err:
            print(err.error_message)
            print(err.status_code,err.error_code)
        except Exception as err:
            print(err)
    
    def check_paper_order(self,side,price,ammount):
        if price*ammount <= 10: # Minimum order size
            return False, 'Order to small.'
        if side == 'BUY': # Check available funds
            return self.CashPosition > ammount*price, 'Not enough funds.'
        if side == 'SELL': # Check available crypto currency
            return self.Position > ammount, 'Not enough funds.'

    def make_paper_order(self,symbol,side,ammount):
        t = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        price = float(self.Client.ticker_price(symbol)['price'])
        op = {'Symbol':symbol, 'Side':side, 'Price':price, 'Ammount':ammount, 'Time':t}
        check = self.check_paper_order(side,price,ammount)
        
        if not check[0]:
            print('Order could not be executed. {}'.format(check[1]))
        else:
            self.Trades.append(op)
            self.refresh_positions(side,price,ammount)
            print('Order: {} {} {} for ${:,.2f} (${:,.2f} total) at {}\n'.format(side,ammount,symbol,price,price*ammount,t))

    def connect_ws(self,handler,symbol,interval,duration):
        self.WebsocketClient.start()
        self.WebsocketClient.kline(
            symbol=symbol,
            interval=interval,
            id=1,
            callback=handler)
        time.sleep(duration)
        self.close_connection()

    def close_connection(self):
        print(pd.DataFrame(self.Trades))
        print('Token position: {:,.4f}'.format(self.Position))
        print('Cash position: {:,.2f}'.format(self.CashPosition))
        print('Commissions: {:,.4f}'.format(self.Commissions))
        price = float(self.Client.ticker_price(self.symbol)['price'])
        print('Total: {:.2f}'.format(self.CashPosition+price*self.Position-self.Commissions))
        self.WebsocketClient.stop()

    def init_candles(self,symbol,interval,lookback):
        return self.candledata_to_list(self.Client.klines(symbol,interval,limit=lookback,endTime=int(time.time()*1000-60000)),symbol,interval)

    def refresh_candles(self,candle,candlelist,maxLen=90000):
        """
        Recieve candlestick data and append to candlestick list
        if it is new candlestick.
        candle: Candlestick dictionary.
        maxLen: Maximum length of list. As new candlesticks enter,
        it removes old candlesticks.
        """
        changed = False

        if candle['k']['x'] == True:
            if candlelist:
                if candle['k']['t'] != candlelist[-1]['t']:
                    candlelist.append(candle['k'])
                    changed = True
                    if len(candlelist) > maxLen:
                        candlelist.pop(0)
            else:
                candlelist.append(candle['k'])
                changed = True
        return candlelist, changed

    def candlelist_to_df(self,candlelist):
        """
        Convert list of candlesticks from WebSocket to DataFrame.
        """
        headers = ['Open time','Close time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
        candledf = pd.DataFrame(candlelist,index=[i for i in range(len(candlelist))])
        candledf.set_axis(headers, axis=1, inplace=True)
        candledf['Open time'] = pd.to_datetime(candledf['Open time'], unit='ms')
        candledf['Close time'] = pd.to_datetime(candledf['Close time'], unit='ms')
        candledf[['Close price','Open price','High price','Low price','Base asset volume']] = candledf[['Close price','Open price','High price','Low price','Base asset volume']].astype('float')
        return candledf[['Open time','Close time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?']]

    def candledata_to_list(self,candledata,symbol,interval):
        """
        Convert candlesticks historic table to candlestick list of dictionaries.
        """
        candlelist = []
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
            candlelist.append(candleDict['k'])
        return candlelist

    def candledata_to_df(self,candledata,symbol,interval):
        """
        Convert candlesticks historic table to DataFrame.
        """
        headers = ['Open time','Open price','High price','Low price','Close price','Base asset volume','Close time','Quote asset volume','Number of trades','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
        candledf = pd.DataFrame(candledata)
        candledf.set_axis(headers, axis=1, inplace=True)
        candledf['Open time'] = pd.to_datetime(candledf['Open time'], unit='ms')
        candledf['Close time'] = pd.to_datetime(candledf['Close time'], unit='ms')
        candledf[['Close price','Open price','High price','Low price','Base asset volume']] = candledf[['Close price','Open price','High price','Low price','Base asset volume']].astype('float')
        candledf['Symbol'] = symbol
        candledf['Interval'] = interval
        candledf['Kline closed?'] = True
        return candledf[['Open time','Close time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume']]
    
    def live_chart(self,symbol,interval,refreshrate):
        def animate(i):
            data = self.candledata_to_df(self.Client.klines(symbol,interval,limit=120),symbol,interval)
            plt.cla()
            plt.plot(data['Close time'],data['Close price'])
            plt.gcf().autofmt_xdate()
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.title(symbol,y=1.05,fontsize=16)
        ani = FuncAnimation(plt.gcf(),animate,refreshrate)
        plt.show()

