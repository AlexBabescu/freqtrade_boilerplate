from pathlib import Path

import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
import pytest
import talib.abstract as ta
from freqtrade.configuration import Configuration, TimeRange
from freqtrade.data.history import load_pair_history
from technical.indicators import ichimoku


class LookaheadBiasException(Exception):
    pass


USER_DATA = Path(__file__).parent.parent

CONFIG = Configuration.from_files(
    [
        str(USER_DATA / "configs" / "config-usdt-binance.json"),
        str(USER_DATA / "configs" / "pairlist-static-usdt-binance.json"),
    ]
)

timerange = "20210601-20211231"
pair = "ADA/USDT"

time_range = TimeRange.parse_timerange(timerange)
dataframe = load_pair_history(
    datadir=USER_DATA / "data" / CONFIG["exchange"]["name"],
    timeframe=CONFIG["timeframe"],
    timerange=time_range,
    pair=pair,
    data_format="jsongz",
)


@pytest.mark.parametrize(
    "indicator_df,indicator_fn,startup_candles",
    [
        pytest.param(
            ta.EMA(dataframe, timeperiod=26),
            lambda dataframe: ta.EMA(dataframe, timeperiod=26),
            26,
            id="ta.EMA",
        ),
        pytest.param(
            qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)["mid"],
            lambda dataframe: qtpylib.bollinger_bands(
                qtpylib.typical_price(dataframe), window=20, stds=2
            )["mid"],
            20,
            id="qtpylib.bollinger_bands",
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
            30,
            marks=pytest.mark.xfail(raises=LookaheadBiasException, strict=True),
            id="technical.indicators.ichimoku",
        ),
    ],
)
def test_indicator_for_lookahead_bias(indicator_df, indicator_fn, startup_candles, request):

    window = 1000
    assert startup_candles < window, "Startup candles should be less than window"

    end = len(dataframe) - len(dataframe) % window

    for idx in range(window, end, window):
        df_slice = dataframe.iloc[idx - window : idx].copy()  # type: ignore
        indicator_slice = indicator_fn(df_slice)

        # We need to remove the startup_candles from the slice
        # This is because some indicators will need N number of candles before they start to work
        indicator_slice = indicator_slice.iloc[idx - window - startup_candles : idx]

        if not np.allclose(indicator_df.iloc[indicator_slice.index], indicator_slice):
            raise LookaheadBiasException(
                f"Indicator {request.node.callspec.id} failed to replicate dataframe. Lookahead bias?"
            )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
