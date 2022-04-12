from datetime import datetime, timezone
from pathlib import Path

import pytest
from freqtrade.configuration import Configuration, TimeRange
from freqtrade.data.dataprovider import DataProvider
from freqtrade.data.history import load_pair_history
from freqtrade.exchange import Exchange
from freqtrade.resolvers import StrategyResolver

USER_DATA = Path(__file__).parent.parent

CONFIG = Configuration.from_files(
    [
        str(USER_DATA / "configs" / "config-usdt-binance.json"),
        str(USER_DATA / "configs" / "pairlist-static-usdt-binance.json"),
    ]
)

DATA_TIMERANGE = TimeRange.parse_timerange("20210101-20211231")


class BTCDropProtectionException(Exception):
    pass


@pytest.mark.parametrize(
    "strategy,pair,btc_drop_timerange",
    [
        pytest.param(
            "AlwaysBuy",
            "COMP/USDT",
            [
                datetime(2021, 5, 9, 0, 0, tzinfo=timezone.utc),
                datetime(2021, 5, 20, 0, 0, tzinfo=timezone.utc),
            ],
            marks=pytest.mark.xfail(raises=BTCDropProtectionException, strict=True),
        ),
        pytest.param(
            "AlwaysBuy",
            "ADA/USDT",
            [
                datetime(2021, 6, 15, 0, 0, tzinfo=timezone.utc),
                datetime(2021, 6, 22, 0, 0, tzinfo=timezone.utc),
            ],
            marks=pytest.mark.xfail(raises=BTCDropProtectionException, strict=True),
        ),
    ],
)
def test_btc_drop_protection(strategy, pair, btc_drop_timerange):
    CONFIG["strategy"] = strategy
    candles = load_pair_history(
        datadir=USER_DATA / "data" / CONFIG["exchange"]["name"],
        timeframe=CONFIG["timeframe"],
        timerange=DATA_TIMERANGE,
        pair=pair,
        data_format="jsongz",
    )

    strategy = StrategyResolver.load_strategy(CONFIG)
    strategy.dp = DataProvider(CONFIG, Exchange(CONFIG), None)

    df = strategy.analyze_ticker(candles.copy(), {"pair": pair})

    for _, row in df.iterrows():
        if time_in_range(btc_drop_timerange[0], btc_drop_timerange[1], row["date"].to_pydatetime()):
            if row["buy"] != 0:
                raise BTCDropProtectionException("BTC drop protection failed")


def time_in_range(start, end, x):
    """
    Return true if x is in the range [start, end]

    >>> import datetime
    >>> start = datetime.time(23, 0, 0)
    >>> end = datetime.time(1, 0, 0)
    >>> time_in_range(start, end, datetime.time(23, 30, 0))
    True
    >>> time_in_range(start, end, datetime.time(12, 30, 0))
    False
    """
    if start <= end:
        return start <= x <= end
    return start <= x or x <= end


if __name__ == "__main__":
    pytest.main(["-s", __file__])
