##################
# Exchange Class #
##################

import os
import time

import matplotlib.pyplot as plt
import pandas as pd
from binance.error import ClientError
from binance.spot import Spot
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from matplotlib.animation import FuncAnimation


class Exchange():

    def __init__(self, api: str, secret: str, paper_portfolio: list[float,float] = [0.1,1000], commission: float = 0.00075, logging: bool = True) -> None:
        self.apiurl = 'https://api.binance.com'
        self.wsurl = 'wss://stream.binance.com:9443/ws'
        self.commission = commission

        self.Client = Spot(key=api, secret=secret, base_url=self.apiurl)
        self.WebsocketClient = SpotWebsocketClient(stream_url=self.wsurl)
        
        self.log_file = os.path.join(os.getcwd(),'log_file.txt')
        self.logging = logging
        self.log_to_file(time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time())),init=True)

        self.Symbol = ''
        self.Trades = []
        self.Position = 0
        self.CashPosition = 0
        self.Commissions = 0
        self.PaperPortfolio = paper_portfolio

    def log_to_file(self, msg: str, init: bool = False) -> None:
        """Log messages to log file for later inspection."""
        if self.logging:
            if init:
                with open(self.log_file,'w') as f:
                    f.write(msg)
            else:
                with open(self.log_file,'a+') as f:
                    f.write('\n'+msg)

    def init_portfolio(self, coin: str, paper_trade: bool) -> None:
        """Initialize local portfolio to track orders and current positions."""
        self.Symbol = coin + 'USDT'
        if paper_trade:
            self.Position = self.PaperPortfolio[0]
            self.CashPosition = self.PaperPortfolio[1]
        else:
            self.Position = self.get_coin_balance(coin)
            self.CashPosition = self.get_coin_balance('USDT')

    def set_paper_portfolio(self, coin_balance: float = 0, cash: float = 0, use_real_balance: bool = False, coin: str = '') -> None:
        """Set paper portfolio values after initializing exchange class."""
        if use_real_balance:
            self.PaperPortfolio[0] = self.get_coin_balance(coin)
            self.PaperPortfolio[1] = self.get_coin_balance('USDT')
        else:
            self.PaperPortfolio[0] = coin_balance
            self.PaperPortfolio[1] = cash

    def account_balance(self) -> pd.DataFrame:
        """Get current account balances from binance."""
        acc_df = pd.DataFrame(self.Client.account()['balances'])
        acc_df[['free','locked']] = acc_df[['free','locked']].astype(float)
        acc_df.columns = ['Asset','Free','Locked']
        acc_df = acc_df.loc[(acc_df['Free'] != 0.0)|(acc_df['Locked'] != 0.0)].reset_index()
        return acc_df[['Asset','Free','Locked']]

    def get_coin_balance(self,coin: str) -> float:
        """Get balance of specific coin."""
        acc_df = self.account_balance()
        return float(acc_df.loc[acc_df['Asset'] == coin,'Free'])

    def refresh_positions(self, side: str, price: float, ammount: float) -> None:
        """Given an order, modify positions accordingly."""
        if side == 'BUY':
            self.Position += ammount
            self.CashPosition -= ammount*price
            self.Commissions += ammount*price*self.commission
        if side == 'SELL':
            self.Position -= ammount
            self.CashPosition += ammount*price
            self.Commissions += ammount*price*self.commission

    def value_positions(self) -> None:
        """Value current positions."""
        price = float(self.Client.ticker_price(self.Symbol)['price'])
        self.Wealth = self.CashPosition+price*self.Position-self.Commissions
        msg = '\n{} position: {:,.4f}\nCash position: {:,.2f}\nCommissions: {:,.2f}\nTotal: {:.2f}\n'.format(self.Symbol,self.Position,self.CashPosition,self.Commissions,self.Wealth)
        print(msg)
        self.log_to_file(msg)

    def market_order(self, symbol: str, side: str, ammount: float) -> None:
        """Send market execution order to binance to get filled."""
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": ammount}
        try:
            order = self.Client.new_order(**params)
            t = time.strftime('%Y-%m-%d %H:%M', time.localtime(order['transactTime']/1000))
            price = float(order['cummulativeQuoteQty'])/float(order['executedQty'])
            op = {'Symbol':symbol, 'Side':side, 'Price':price, 'Ammount':ammount, 'Time':t}
            self.Trades.append(op)
            self.refresh_positions(side,price,ammount)
            msg = 'Order: {} {} {} for ${:,.2f} (${:,.2f} total) at {}'.format(side,ammount,symbol,price,price*ammount,t)
            print(msg)
            self.log_to_file(msg)
        except ClientError as err:
            msg = '{} order could not be executed. {} {} {}'.format(side,err.error_message,err.status_code,err.error_code)
            print(msg)
            self.log_to_file(msg)
    
    def check_paper_order(self, side: str, price: float, ammount: float) -> tuple[bool,str]:
        """Check if a paper order can be executed based on current cash and coin positions."""
        if price*ammount <= 10: # Minimum order size
            return False, 'Order to small.'
        if side == 'BUY': # Check available funds
            return self.CashPosition > ammount*price, 'Not enough funds.'
        if side == 'SELL': # Check available crypto currency
            return self.Position > ammount, 'Not enough funds.'

    def paper_market_order(self, symbol: str, side: str, ammount: float) -> None:
        """Execute paper order that is stored and handled localy."""
        t = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        price = float(self.Client.ticker_price(symbol)['price'])
        op = {'Symbol':symbol, 'Side':side, 'Price':price, 'Ammount':ammount, 'Time':t}
        check = self.check_paper_order(side,price,ammount)
        if not check[0]:
            msg = '{} order could not be executed. {}'.format(side,check[1])
            print(msg)
            self.log_to_file(msg)
        else:
            self.Trades.append(op)
            self.refresh_positions(side,price,ammount)
            msg = 'Order: {} {} {} for ${:,.2f} (${:,.2f} total) at {}'.format(side,ammount,symbol,price,price*ammount,t)
            print(msg)
            self.log_to_file(msg)

    def connect_ws(self, handler: callable, symbol: str, interval: str, duration: int) -> None:
        """Connect to WebSocket."""
        self.WebsocketClient.start()
        self.WebsocketClient.kline(
            symbol=symbol,
            interval=interval,
            id=1,
            callback=handler)
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
        finally:
            self.close_connection()

    def close_connection(self) -> None:
        """Close connection to WebSocket, print current positions and deals made this session."""
        print('\nClosing connection.')
        print(pd.DataFrame(self.Trades).to_string(index=False))
        self.log_to_file(pd.DataFrame(self.Trades).to_string(index=False))
        self.value_positions()
        print('Number of trades: {}'.format(len(self.Trades)))
        self.log_to_file(time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time())))
        self.WebsocketClient.stop()

    def init_candles(self, symbol: str, interval: str, lookback: int) -> list[dict]:
        """Get historic data for strategies that need to look back to function."""
        kline_data = self.Client.klines(symbol,interval,limit=lookback,endTime=int(time.time()*1000-60000))
        return self.candledata_to_list(kline_data,symbol,interval)

    def refresh_candles(self, candle: dict, candlelist: list[dict] , maxLen: int = 90000) -> tuple[list[dict],bool]:
        """Recieve candlestick data and append to candlestick list if it is new candlestick."""
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

    def candlelist_to_df(self, candlelist: list[dict]) -> pd.DataFrame:
        """Convert list of candlesticks from WebSocket to DataFrame."""
        headers = ['Open time','Close time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
        candledf = pd.DataFrame(candlelist,index=[i for i in range(len(candlelist))])
        candledf.set_axis(headers, axis=1, inplace=True)
        candledf['Open time'] = pd.to_datetime(candledf['Open time'], unit='ms')
        candledf['Close time'] = pd.to_datetime(candledf['Close time'], unit='ms')
        candledf[['Close price','Open price','High price','Low price','Base asset volume']] = candledf[['Close price','Open price','High price','Low price','Base asset volume']].astype('float')
        return candledf[['Open time','Close time','Symbol','Interval','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?']]

    def candledata_to_list(self, candledata: list[list], symbol: str, interval: str) -> list[dict]:
        """Convert candlesticks historic table to candlestick list of dictionaries."""
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

    def candledata_to_df(self, candledata: list[list], symbol: str, interval: str) -> pd.DataFrame:
        """Convert candlesticks historic table to DataFrame."""
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
    
    def live_chart(self, symbol: str, interval: str, refreshrate: int = 2000) -> None:
        """Plot live chart of selected coin."""
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
