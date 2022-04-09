import pytest
from pathlib import Path

from freqtrade.configuration import Configuration
from freqtrade.data.dataprovider import DataProvider
from freqtrade.data.history import load_pair_history
from freqtrade.resolvers import StrategyResolver
from freqtrade.configuration import TimeRange

USER_DATA = Path(__file__).parent.parent

config = Configuration.from_files(
    [
        str(USER_DATA / "configs" / "config-usdt-binance.json"),
        str(USER_DATA / "configs" / "pairlist-static-usdt-binance.json"),
    ]
)


@pytest.mark.parametrize(
    "strategy,pair,timerange",
    [
        ("SampleStrategy", "COMP/USDT", "20211201-20211231"),
        ("SampleStrategy", "ADA/USDT", "20211001-20211231"),
        # pytest.param("LookaheadStrategy", "COMP/USDT", "20211201-20211231", marks=pytest.mark.xfail),
    ],
)
def test_lookahead(strategy, pair, timerange):
    config["strategy"] = strategy
    time_range = TimeRange.parse_timerange(timerange)
    candles = load_pair_history(
        datadir=USER_DATA / "data" / config["exchange"]["name"],
        timeframe=config["timeframe"],
        timerange=time_range,
        pair=pair,
        data_format="jsongz",
    )

    strategy = StrategyResolver.load_strategy(config)
    strategy.dp = DataProvider(config, None, None)

    df = strategy.analyze_ticker(candles, {"pair": pair})

    buy_signals = df[df["buy"] == 1][["date", "close"]]
    sell_signals = df[df["sell"] == 1][["date", "close"]]

    assert True
