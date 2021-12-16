###################################
# Example Account Balances Script #
###################################

import os
from binancetrading import Account

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')

APIURL = 'https://api.binance.com'

account = Account(API, SECRET, paper_trade=False, apiurl=APIURL)
balances = account.account_balances()

print(balances)
