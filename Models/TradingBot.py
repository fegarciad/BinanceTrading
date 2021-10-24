#######################
# Main Traiding Class #
#######################

import os
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from binance.spot import Spot
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from config import API_KEY, API_SECRET

from Models.Utils import ema, macd, rsi, sma
from Models.Exchange import (candleListToDF, candleToDF, candleToList,
                              refreshCandles)

cd = os.getcwd()+'\\'

class TradingBot():

    def __init__(self):
        pass


