# pylint: disable=pointless-string-statement
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import pytest
import talib.abstract as ta
from freqtrade.data.history import load_pair_history
from technical.indicators import ichimoku

"""
Test for indicator consistency

This test is to verify that the a indicator is the same for a given pair when
calculated over a large dataframe (like we do in backtesting)
and when calculated over a small dataframe (like we do in live trading).

For example:
Imaging we have a large dataframe with 10000 candles and a small dataframe with 999 candles.
                                             A
                                     1000--------1999
                                     |              |
          0                                                                    10000
indicator(.....................................................................)
                                              |     |
                                              -------
                                                 C

                  B
          1000--------1999
          |              |
indicator(................)
                   |     |
                   -------
                      D


len(A) == len(B) == 999
len(C) == len(D) == no_of_last_candles_to_compare

A is calculated over a large dataframe then sliced out
B is calculated over a small dataframe.


We then compare C and D and raise an exception if they are not the same (within 1.0e-5 tolerance)
"""


class ConsistencyException(Exception):
    pass


pair = "ADA/USDT"

dataframe = load_pair_history(
    datadir=pytest.user_data / "data" / pytest.config["exchange"]["name"],
    timeframe=pytest.config["timeframe"],
    timerange=pytest.data_timerange,
    pair=pair,
    data_format="jsongz",
)


def EWO(dataframe, ema_length=5, ema2_length=35):
    df = dataframe.copy()
    ema1 = ta.EMA(df, timeperiod=ema_length)
    ema2 = ta.EMA(df, timeperiod=ema2_length)
    emadif = (ema1 - ema2) / df["low"] * 100
    return emadif


@pytest.mark.parametrize(
    "indicator_df,indicator_fn",
    [
        pytest.param(
            qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)["mid"],
            lambda dataframe: qtpylib.bollinger_bands(
                qtpylib.typical_price(dataframe), window=20, stds=2
            )["mid"],
            id="qtpylib.bollinger_bands",
        ),
        pytest.param(
            ta.EMA(dataframe, timeperiod=26),
            lambda dataframe: ta.EMA(dataframe, timeperiod=26),
            id="ta.EMA 26",
        ),
        pytest.param(
            ta.EMA(dataframe, timeperiod=183),
            lambda dataframe: ta.EMA(dataframe, timeperiod=183),
            marks=pytest.mark.xfail(raises=ConsistencyException, strict=True),
            id="ta.EMA 183",
        ),
        pytest.param(
            EWO(dataframe, 20, 90), lambda dataframe: EWO(dataframe, 20, 90), id="EWO 20 90",
        ),
        pytest.param(
            EWO(dataframe, 50, 200),
            lambda dataframe: EWO(dataframe, 50, 200),
            marks=pytest.mark.xfail(raises=ConsistencyException, strict=True),
            id="EWO 50 200",
        ),
        pytest.param(
            ichimoku(
                dataframe,
                conversion_line_period=20,
                base_line_periods=60,
                laggin_span=120,
                displacement=30,
            )["chikou_span"],
            lambda dataframe: ichimoku(
                dataframe,
                conversion_line_period=20,
                base_line_periods=60,
                laggin_span=120,
                displacement=30,
            )["chikou_span"],
            marks=pytest.mark.xfail(raises=ConsistencyException, strict=True),
            id="technical.indicators.ichimoku",
        ),
    ],
)
def test_indicator_for_consistency(indicator_df, indicator_fn, request):

    # Number of candles to typically get from the exchange
    window = 999

    no_of_last_candles_to_compare = 200

    end = len(dataframe) - len(dataframe) % window

    for idx in range(window, end, window):
        df_slice = dataframe.iloc[idx - window : idx].copy()  # type: ignore
        assert len(df_slice) == window, f"Slice should be of length {window}"
        full_indicator_slice = indicator_fn(df_slice)

        # We need to remove the startup_candles from the slice
        # This is because some indicators will need N number of candles before they start to work
        indicator_slice = full_indicator_slice.loc[idx - no_of_last_candles_to_compare : idx].copy()

        assert (
            len(indicator_slice) == no_of_last_candles_to_compare
        ), f"Indicator slice should be of length {no_of_last_candles_to_compare}"

        if not np.allclose(
            indicator_df.loc[indicator_slice.index], indicator_slice, rtol=1.0e-5, atol=1.0e-5,
        ):
            raise ConsistencyException(
                f"Indicator {request.node.callspec.id} failed to replicate dataframe."
            )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
