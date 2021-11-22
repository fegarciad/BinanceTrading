##################
# Exchange Class #
##################

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
        
        self.Account = account
        self.WebsocketClient = SpotWebsocketClient(stream_url=wsurl)
        self.commission = commission

    def execute_order(self, symbol: str, side: str, ammount: float, paper_trade: bool) -> None:
        """Send market execution order to Binance or execute paper trade."""
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": ammount}
        try: 
            if not paper_trade:
                confirmation = self.Account.Client.new_order(**params)
                order = MarketOrder(confirmation,self.commission)
            else:
                order = PaperOrder(params,self.commission)
                order.set_price(float(self.Account.Client.ticker_price(symbol)['price']))
                self.check_paper_order(order.side,order.price,order.qty)
            self.Account.trades.append(order.order_dict)
            self.Account.refresh_positions(order.side,order.price,order.qty,order.commission)
            print('\n'+str(order))
            self.Account.log_to_file('\n'+str(order))
        except ClientError as err:
            msg = '\n{} order could not be executed. {} {} {}'.format(side,err.error_message,err.status_code,err.error_code)
            print(msg)
            self.Account.log_to_file(msg)
    
    def check_paper_order(self, side: str, price: float, ammount: float) -> None:
        """Check if a paper order can be executed based on current cash and coin positions."""
        if price*ammount <= 10: # Minimum order size
            raise ClientError('','','Order to small.','')
        if side == 'BUY' and self.Account.cash_position < ammount*price: # Check available funds
            raise ClientError('','','Not enough funds.','')
        if side == 'SELL' and self.Account.position < ammount: # Check available crypto currency
            raise ClientError('','','Not enough funds.','')
    
    def exit_positions(self) -> None:
        """Exit positions when returns hit stop loss."""
        pass

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
            self.Account.log_to_file('\nKeyboardInterrupt')
        finally:
            self.close_connection(symbol)

    def close_connection(self, symbol: str) -> None:
        """Close connection to WebSocket, print current positions and deals made this session."""
        print('\nClosing connection.')
        print('\nNumber of trades: {}'.format(len(self.Account.trades)))
        print(pd.DataFrame(self.Account.trades).to_string(index=False))
        self.Account.log_to_file('\nNumber of trades: {}\n{}'.format(len(self.Account.trades),pd.DataFrame(self.Account.trades).to_string(index=False)))
        self.Account.value_positions(symbol)
        msg = '\nReturn: {:.2f}'.format(self.Account.wealth - self.Account.init_wealth)
        print(msg+'\n')
        self.Account.log_to_file('{}\n\nFinished at: {}'.format(msg,time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))))
        self.WebsocketClient.stop()

    def init_candles(self, symbol: str, interval: str, lookback: int) -> list[dict]:
        """Get historic data for strategies that need to look back to function."""
        kline_data = self.Account.Client.klines(symbol,interval,limit=lookback,endTime=int(time.time()*1000-60000))
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
            data = self.candledata_to_df(self.Account.Client.klines(symbol,interval,limit=120),symbol,interval)
            plt.cla()
            plt.plot(data['Close time'],data['Close price'])
            plt.gcf().autofmt_xdate()
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.title(symbol,y=1.05,fontsize=16)
        ani = FuncAnimation(plt.gcf(),animate,refreshrate)
        plt.show()
