
"""Exchange Class"""

import threading
import time
from typing import Callable

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from binance.error import ClientError
from binance.websocket.spot.websocket_client import SpotWebsocketClient

import binancetrading as bt


class Exchange:
    """Exchange class."""

    def __init__(self, account: bt.Account, commission: float = 0.00075, wsurl: str = 'wss://stream.binance.com:9443/ws') -> None:
        self.account = account
        self.websocketclient = SpotWebsocketClient(stream_url=wsurl)
        self.commission = commission
        self.event = threading.Event()
        self.connection: TimedValue = TimedValue(0)

    def execute_order(self, symbol: str, side: str, ammount: float, paper_trade: bool) -> None:
        """Send market execution order to Binance or execute paper trade."""
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": ammount}
        try:
            if not paper_trade:
                confirmation = self.account.client.new_order(**params)
                order = bt.MarketOrder(confirmation, self.commission)
            else:
                order = bt.PaperOrder(params, self.commission)
                order.set_price(float(self.account.client.ticker_price(symbol)['price']))
                self.check_paper_order(order.side, order.price, order.qty)
            self.account.trades.append(order.order_dict)
            self.account.refresh_positions(order.side, order.price, order.qty, order.commission)
            print('\n' + str(order))
            self.account.log_to_file('\n' + str(order))
        except ClientError as error:
            msg = f'\n{side} order could not be executed. {error.error_message} {error.status_code} {error.error_code}'
            print(msg)
            self.account.log_to_file(msg)

    def check_paper_order(self, side: str, price: float, ammount: float) -> None:
        """Check if a paper order can be executed based on current cash and coin positions."""
        if price * ammount <= 10:  # Minimum order size
            raise ClientError('', '', 'Order to small.', '')
        if side == 'BUY' and self.account.cash_position < ammount * price:  # Check available funds
            raise ClientError('', '', 'Not enough funds.', '')
        if side == 'SELL' and self.account.position < ammount:  # Check available crypto currency
            raise ClientError('', '', 'Not enough funds.', '')

    def exit_positions(self, symbol: str, paper_trade: bool) -> None:
        """Exit positions when returns hit stop loss."""
        to_sell = self.account.position * 0.1
        msg = f'\nExiting {symbol} positions.'
        print(msg)
        self.account.log_to_file(msg)
        self.execute_order(symbol, 'SELL', to_sell, paper_trade)

    def connect_ws(self, handler: Callable[[str], None], symbol: str, interval: str, duration: int) -> None:
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
        msg = f'\nNumber of trades: {self.account.trades}\n{pd.DataFrame(self.account.trades).to_string(index=False)}'
        print(msg)
        self.account.log_to_file(msg)
        self.account.value_positions(symbol)
        msg = f'\nReturn: {self.account.wealth - self.account.init_wealth:.2f} ({(self.account.wealth / self.account.init_wealth - 1) * 100:.2f}%)'
        print(msg + '\n')
        self.account.log_to_file(f'{msg}\n\nFinished at: {time.strftime("%Y-%m-%d %H:%M", time.localtime())}')
        self.websocketclient.stop()

    def init_candles(self, symbol: str, interval: str, lookback: int) -> list[dict]:
        """Get historic data for strategies that need to look back to function."""
        kline_data = self.account.client.klines(symbol, interval, limit=lookback, endTime=int(time.time() * 1000 - 60000))
        return self.candledata_to_list(kline_data, symbol, interval)

    def refresh_candles(self, candle: dict, candlelist: list[dict], max_len: int = 90000) -> tuple[list[dict], bool]:
        """Recieve candlestick data and append to candlestick list if it is new candlestick."""
        changed = False
        if candle['k']['x']:
            if candlelist:
                if candle['k']['t'] != candlelist[-1]['t']:
                    candlelist.append(candle['k'])
                    changed = True
                    if len(candlelist) > max_len:
                        candlelist.pop(0)
            else:
                candlelist.append(candle['k'])
                changed = True
        return candlelist, changed

    def candle_list_to_df(self, candle_list: list[dict]) -> pd.DataFrame:
        """Convert list of candlesticks from WebSocket to DataFrame."""
        headers = [
            'Open time', 'Close time', 'Symbol', 'Interval', 'First trade ID', 'Last trade ID',
            'Open price', 'Close price', 'High price', 'Low price', 'Base asset volume',
            'Number of trades', 'Kline closed?', 'Quote asset volume', 'Taker buy base asset volume',
            'Taker buy quote asset volume', 'Ignore']
        candle_df = pd.DataFrame(candle_list, index=[i for i, _ in enumerate(candle_list)])
        candle_df.set_axis(headers, axis=1, inplace=True)
        candle_df['Open time'] = pd.to_datetime(candle_df['Open time'], unit='ms')
        candle_df['Close time'] = pd.to_datetime(candle_df['Close time'], unit='ms')
        candle_df[['Close price', 'Open price', 'High price', 'Low price', 'Base asset volume']]\
            = candle_df[['Close price', 'Open price', 'High price', 'Low price', 'Base asset volume']].astype('float')
        return candle_df[[
            'Open time', 'Close time', 'Symbol', 'Interval', 'Open price', 'Close price',
            'High price', 'Low price', 'Base asset volume', 'Number of trades']]

    def candledata_to_list(self, candle_data: list[list], symbol: str, interval: str) -> list[dict]:
        """Convert candlesticks historic table to candlestick list of dictionaries."""
        candle_list = []
        for candle in candle_data:
            candle_dict = {
                "t": candle[0],   # Kline start time
                "T": candle[6],   # Kline close time
                "s": symbol,      # Symbol
                "i": interval,    # Interval
                "f": 0,           # First trade ID
                "L": 0,           # Last trade ID
                "o": candle[1],   # Open price
                "c": candle[4],   # Close price
                "h": candle[2],   # High price
                "l": candle[3],   # Low price
                "v": candle[5],   # Base asset volume
                "n": candle[8],   # Number of trades
                "x": True,        # Is this kline closed?
                "q": candle[7],   # Quote asset volume
                "V": candle[9],   # Taker buy base asset volume
                "Q": candle[10],  # Taker buy quote asset volume
                "B": candle[11]   # Ignore
            }
            candle_list.append(candle_dict)
        return candle_list

    def candledata_to_df(self, candledata: list[list], symbol: str, interval: str) -> pd.DataFrame:
        """Convert candlesticks historic table to DataFrame."""
        headers = [
            'Open time', 'Open price', 'High price', 'Low price',
            'Close price', 'Base asset volume', 'Close time', 'Quote asset volume',
            'Number of trades', 'Taker buy base asset volume',
            'Taker buy quote asset volume', 'Ignore']
        candle_df = pd.DataFrame(candledata)
        candle_df.set_axis(headers, axis=1, inplace=True)
        candle_df['Open time'] = pd.to_datetime(candle_df['Open time'], unit='ms')
        candle_df['Close time'] = pd.to_datetime(candle_df['Close time'], unit='ms')
        candle_df[['Close price', 'Open price', 'High price', 'Low price', 'Base asset volume']]\
            = candle_df[['Close price', 'Open price', 'High price', 'Low price', 'Base asset volume']].astype('float')
        candle_df['Symbol'] = symbol
        candle_df['Interval'] = interval
        candle_df['Kline closed?'] = True
        return candle_df[[
            'Open time', 'Close time', 'Symbol', 'Interval', 'Open price', 'Close price',
            'High price', 'Low price', 'Base asset volume', 'Number of trades']]

    def live_chart(self, coin: str, interval: str, refreshrate: int = 2000) -> None:
        """Plot live chart of selected coin."""
        symbol = coin + 'USDT'

        def animate(_):
            data = self.candledata_to_df(self.account.client.klines(symbol, interval, limit=120), symbol, interval)
            plt.cla()
            plt.plot(data['Close time'], data['Close price'])
            plt.gcf().autofmt_xdate()
            plt.gca().yaxis.set_major_formatter('{x:,.2f}')
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.title(symbol, y=1.05, fontsize=16)
        _ = FuncAnimation(plt.gcf(), animate, refreshrate)
        plt.show()


class TimedValue:
    """Timed value class."""

    def __init__(self, duration: int) -> None:
        self.duration = duration
        self.started_at = time.time()

    @property
    def is_running(self) -> bool:
        """Check if instance has expired."""
        time_passed = time.time() - self.started_at
        if time_passed > self.duration:
            return False
        return True
