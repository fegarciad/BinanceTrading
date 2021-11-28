##################
# Exchange Class #
##################

import threading
import time
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation

from binance.error import ClientError
from binance.websocket.spot.websocket_client import SpotWebsocketClient

from Models.Account import Account
from Models.Orders import MarketOrder, PaperOrder


class Exchange:

    def __init__(self, account: Account, commission: float = 0.00075, wsurl: str = 'wss://stream.binance.com:9443/ws') -> None:
        
        self.account = account
        self.websocketclient = SpotWebsocketClient(stream_url=wsurl)
        self.commission = commission
        self.event = threading.Event()

    def execute_order(self, symbol: str, side: str, ammount: float, paper_trade: bool) -> None:
        """Send market execution order to Binance or execute paper trade."""
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": ammount}
        try: 
            if not paper_trade:
                confirmation = self.account.Client.new_order(**params)
                order = MarketOrder(confirmation,self.commission)
            else:
                order = PaperOrder(params,self.commission)
                order.set_price(float(self.account.Client.ticker_price(symbol)['price']))
                self.check_paper_order(order.side,order.price,order.qty)
            self.account.trades.append(order.order_dict)
            self.account.refresh_positions(order.side,order.price,order.qty,order.commission)
            print('\n'+str(order))
            self.account.log_to_file('\n'+str(order))
        except ClientError as err:
            msg = '\n{} order could not be executed. {} {} {}'.format(side,err.error_message,err.status_code,err.error_code)
            print(msg)
            self.account.log_to_file(msg)
    
    def check_paper_order(self, side: str, price: float, ammount: float) -> None:
        """Check if a paper order can be executed based on current cash and coin positions."""
        if price*ammount <= 10: # Minimum order size
            raise ClientError('','','Order to small.','')
        if side == 'BUY' and self.account.cash_position < ammount*price: # Check available funds
            raise ClientError('','','Not enough funds.','')
        if side == 'SELL' and self.account.position < ammount: # Check available crypto currency
            raise ClientError('','','Not enough funds.','')

    def exit_positions(self, symbol: str, paper_trade: bool) -> None:
        """Exit positions when returns hit stop loss."""
        to_sell = self.account.position * 0.1
        msg = '\nExiting {} positions.'.format(symbol)
        print(msg)
        self.account.log_to_file(msg)
        self.execute_order(symbol,'SELL',to_sell,paper_trade)

    def connect_ws(self, handler: callable, symbol: str, interval: str, duration: int) -> None:
        """Connect to WebSocket."""
        self.websocketclient.start()
        self.websocketclient.kline(
            symbol=symbol,
            interval=interval,
            id=1,
            callback=handler)
        self.connection = TimedValue(duration)
        try:
            while self.connection.is_running and not self.event.is_set():
                pass
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')
            self.account.log_to_file('\nKeyboardInterrupt')
            self.event.set()
        self.close_connection(symbol)
        
    def close_connection(self, symbol: str) -> None:
        """Close connection to WebSocket, print current positions and deals made this session."""
        print('\nClosing connection.')
        msg = '\nNumber of trades: {}\n{}'.format(len(self.account.trades),pd.DataFrame(self.account.trades).to_string(index=False))
        print(msg)
        self.account.log_to_file(msg)
        self.account.value_positions(symbol)
        msg = '\nReturn: {:.2f} ({:.2f}%)'.format(self.account.wealth - self.account.init_wealth,(self.account.wealth/self.account.init_wealth - 1)*100)
        print(msg+'\n')
        self.account.log_to_file('{}\n\nFinished at: {}'.format(msg,time.strftime('%Y-%m-%d %H:%M', time.localtime())))
        self.websocketclient.stop()

    def init_candles(self, symbol: str, interval: str, lookback: int) -> list[dict]:
        """Get historic data for strategies that need to look back to function."""
        kline_data = self.account.Client.klines(symbol,interval,limit=lookback,endTime=int(time.time()*1000-60000))
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

    def candle_list_to_df(self, candle_list: list[dict]) -> pd.DataFrame:
        """Convert list of candlesticks from WebSocket to DataFrame."""
        headers = ['Open time','Close time','Symbol','Interval','First trade ID','Last trade ID','Open price','Close price','High price','Low price','Base asset volume','Number of trades','Kline closed?','Quote asset volume','Taker buy base asset volume','Taker buy quote asset volume','Ignore']
        candledf = pd.DataFrame(candle_list,index=[i for i,_ in enumerate(candle_list)])
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
            data = self.candledata_to_df(self.account.Client.klines(symbol,interval,limit=120),symbol,interval)
            plt.cla()
            plt.plot(data['Close time'],data['Close price'])
            plt.gcf().autofmt_xdate()
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.title(symbol,y=1.05,fontsize=16)
        ani = FuncAnimation(plt.gcf(),animate,refreshrate)
        plt.show()


class TimedValue:
    def __init__(self, duration: int) -> None:
        self.duration = duration
        self.killed = False
        self._started_at = time.time()

    @property
    def is_running(self) -> None:
        time_passed = time.time() - self._started_at
        if time_passed > self.duration:
            return False
        return True