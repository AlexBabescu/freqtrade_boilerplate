from functools import reduce

import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta
from freqtrade.strategy import merge_informative_pair
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class AlwaysBuy(IStrategy):

    # ROI table:
    # fmt: off
    minimal_roi = {
        "0": 1,
        "100": 2,
        "200": 3,
        "300": -1
        }
    # fmt: on

    # Stoploss:
    stoploss = -0.2

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True
    # Buy hypers
    timeframe = "5m"
    use_sell_signal = False
    # #################### END OF RESULT PLACE ####################

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[:, "buy"] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        return dataframe
