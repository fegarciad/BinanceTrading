# BinanceTrading

BinanceTrading is a custom trading library using the Binance API for executing or backtesting trading strategies. It is hardcoded to only trade coins against USD Tether.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install.

```bash
pip install binancetrading
```

If you are on windows, follow these [instructions](https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2) to be able to use Binance websocket client.

## Usage
To use this library it is necesary to have Binance API keys, it is also possible to work with Binance Testnet keys. Here we store them as environment variables.

Get the current coin balances in the account.
```python
import os
from binancetrading import Account

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')

account = Account(API, SECRET, paper_trade=False, apiurl='https://api.binance.com')
balances = account.account_balances()

print(balances)
```

Print the last ten 1 minute candlesticks of BTCUSDT.
```python
from binancetrading import Exchange

exchange = Exchange()
data = exchange.kline_df('BTC', '1m', 10)

print(data)
```
See more [examples](https://github.com/fegarciad/BinanceTrading/tree/main/examples).

## Modules

### Account

The account class is where all the relevant account data is stored like cash and token positions. It has methods to retrieve balances and these are updated if a trade is made.

### Exchange

The exchange module is responsible for retrieving data from the Binance API using websockets and requests. It is also responsible for executing trades.

### Trading bot

To trade and test stragies it is necessary to create an instance of an trading bot, which will retrieve data from the exchange and execute orders given by the strategy. These trades are made by an account instance.

### Strategies

The strategies module contains the trading strategies to use. These are basic starting points and it is encouraged to implement own strategies. These should follow the TradingStrategy abstract base class.

### Backtesting

The backtesting module is to make an event driven trading strategy backtest. It also prints price charts with entry and exit points given by the strategy.

## Further development

Include an strategy optimizer module to optimize the parameters of a trading strategy using backtest results.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)