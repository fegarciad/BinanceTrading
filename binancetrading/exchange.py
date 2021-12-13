
"""Exchange Class"""

import threading
import time
from typing import Callable

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from binance.error import ClientError
from binance.spot import Spot
from binance.websocket.spot.websocket_client import SpotWebsocketClient

from binancetrading.account import Account, log_msg
from binancetrading.orders import MarketOrder, PaperOrder


class Exchange:
    """Exchange class."""

    def __init__(self, wsurl: str = 'wss://stream.binance.com:9443/ws') -> None:
        self.websocketclient = SpotWebsocketClient(stream_url=wsurl)
        self.event = threading.Event()
        self.connection: TimedValue = TimedValue(0)

    def execute_order(self, account: Account, symbol: str, side: str, ammount: float, commission: float, paper_trade: bool) -> None:
        """Send market execution order to Binance or execute paper trade."""
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": str(ammount)}
        try:
            if not paper_trade:
                confirmation = account.client.new_order(**params)
                order = MarketOrder(confirmation, commission)
            else:
                order = PaperOrder(params, commission)
                order.set_price(float(account.client.ticker_price(symbol)['price']))
                self._check_paper_order(account, order.side, order.price, order.qty)
            account.trades.append(order.order_dict)
            account._refresh_positions(order.side, order.price, order.qty, order.commission)
            log_msg('\n' + str(order), verb=True)
        except ClientError as error:
            log_msg(f'\n{side} order could not be executed. {error.error_message} {error.status_code} {error.error_code}')

    def kline_df(self, coin: str, interval: str, lookback: int) -> pd.DataFrame:
        """Return DataFrame with historic candlestick data."""
        symbol = coin + 'USDT'
        client = Spot()
        kline_data = client.klines(symbol, interval, limit=lookback, endTime=int(time.time() * 1000 - 60000))
        return _candle_data_to_df(kline_data, symbol, interval)

    def live_chart(self, coin: str, interval: str, refreshrate: int = 2000) -> None:
        """Plot live chart of selected coin."""
        symbol = coin + 'USDT'
        client = Spot()

        def animate(_):
            data = _candle_data_to_df(client.klines(symbol, interval, limit=120), symbol, interval)
            plt.cla()
            plt.plot(data['Close time'], data['Close price'])
            plt.gcf().autofmt_xdate()
            plt.gca().yaxis.set_major_formatter('{x:,.2f}')
            plt.xlabel('Time')
            plt.ylabel('Price')
            plt.title(symbol, y=1.05, fontsize=16)
        _ = FuncAnimation(plt.gcf(), animate, refreshrate)
        plt.show()

    def exit_positions(self, account: Account, symbol: str, paper_trade: bool) -> None:
        """Exit positions of a coin."""
        percentage_to_sell = 0.1
        to_sell = account.position * percentage_to_sell
        log_msg(f'\nExiting {1 - percentage_to_sell}% of {symbol} positions.')
        self.execute_order(account, symbol, 'SELL', to_sell, 0.0, paper_trade)

    def _check_paper_order(self, account: Account, side: str, price: float, ammount: float) -> None:
        """Check if a paper order can be executed based on current cash and coin positions."""
        if price * ammount <= 10:  # Minimum order size
            raise ClientError('', '', 'Order to small.', '')
        if side == 'BUY' and account.cash_position < ammount * price:  # Check available funds
            raise ClientError('', '', 'Not enough funds.', '')
        if side == 'SELL' and account.position < ammount:  # Check available crypto currency
            raise ClientError('', '', 'Not enough funds.', '')

    def _connect_ws(self, account: Account, handler: Callable[[dict], None], symbol: str, interval: str, duration: int) -> None:
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
            log_msg('\nKeyboardInterrupt', verb=True)
            self.event.set()
        self._close_connection(account, symbol)

    def _close_connection(self, account: Account, symbol: str) -> None:
        """Close connection to WebSocket, print current positions and deals made this session."""
        print('\nClosing connection.')
        log_msg(f'\nNumber of trades: {len(account.trades)}\n\n{pd.DataFrame(account.trades).to_string(index=False)}', verb=True)
        account._value_positions(symbol)
        log_msg(f'\nReturn: {account.wealth - account.init_wealth:.2f} ({(account.wealth / account.init_wealth - 1) * 100:.2f}%)', verb=True)
        log_msg(f'\nFinished at: {time.strftime("%Y-%m-%d %H:%M", time.localtime())}', verb=True)
        self.websocketclient.stop()

    def _init_candles(self, symbol: str, interval: str, lookback: int) -> list[dict]:
        """Get historic data for strategies that need to look back to function."""
        client = Spot()
        kline_data = client.klines(symbol, interval, limit=lookback, endTime=int(time.time() * 1000 - 60000))
        return _candle_data_to_list(kline_data, symbol, interval)

    def _get_commission(self, account: Account, symbol: str) -> float:
        """Get commission for a coin."""
        # Try except needed because testnet has no commission atribute
        try:
            commission_list = account.client.trade_fee()
        except ClientError:
            return 0.0
        for item in commission_list:
            if item['symbol'] == symbol:
                return item['takerCommission']
        return 0.0


# Helper functions to manipulate binance streaming data

def _refresh_candles(candle: dict, candlelist: list[dict], max_len: int = 10000) -> tuple[list[dict], bool]:
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


def _candle_list_to_df(candle_list: list[dict]) -> pd.DataFrame:
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
    return candle_df[['Open time', 'Close time', 'Symbol', 'Interval', 'Open price', 'Close price',
                      'High price', 'Low price', 'Base asset volume', 'Number of trades']]


def _candle_data_to_list(candle_data: list[list], symbol: str, interval: str) -> list[dict]:
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


def _candle_data_to_df(candledata: list[list], symbol: str, interval: str) -> pd.DataFrame:
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
    return candle_df[['Open time', 'Close time', 'Symbol', 'Interval', 'Open price', 'Close price',
                      'High price', 'Low price', 'Base asset volume', 'Number of trades']]


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
