from functools import reduce

import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class LookaheadStrategy(IStrategy):

    # Buy hyperspace params:
    buy_params = {
        "buy_fast": 2,
        "buy_push": 1.022,
        "buy_shift": -8,
        "buy_slow": 16,
    }

    # Sell hyperspace params:
    sell_params = {
        "sell_fast": 34,
        "sell_push": 0.458,
        "sell_shift": -8,
        "sell_slow": 44,
    }

    # ROI table:
    # fmt: off
    minimal_roi = {
        "0": 0.166,
        "44": 0.012,
        "59": 0
        }
    # fmt: on

    # Stoploss:
    stoploss = -0.194

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True
    # Buy hypers
    timeframe = "5m"
    # #################### END OF RESULT PLACE ####################

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["buy_ema_fast"] = ta.SMA(dataframe, timeperiod=self.buy_params["buy_fast"])
        dataframe["buy_ema_slow"] = ta.SMA(dataframe, timeperiod=self.buy_params["buy_slow"])

        dataframe["sell_ema_fast"] = ta.SMA(dataframe, timeperiod=self.sell_params["sell_fast"])
        dataframe["sell_ema_slow"] = ta.SMA(dataframe, timeperiod=self.sell_params["sell_slow"])

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []

        conditions.append(
            qtpylib.crossed_above(
                dataframe["buy_ema_fast"].shift(self.buy_params["buy_shift"]),
                dataframe["buy_ema_slow"].shift(self.buy_params["buy_shift"])
                * self.buy_params["buy_push"],
            )
        )

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "buy"] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions = []

        conditions.append(
            qtpylib.crossed_below(
                dataframe["sell_ema_fast"].shift(self.sell_params["sell_shift"]),
                dataframe["sell_ema_slow"].shift(self.sell_params["sell_shift"])
                * self.sell_params["sell_push"],
            )
        )

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "sell"] = 1
        return dataframe
