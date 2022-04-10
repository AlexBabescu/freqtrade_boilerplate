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


class LookaheadBiasException(Exception):
    pass


@pytest.mark.parametrize(
    "strategy,pair,timerange",
    [
        ("SampleStrategy", "COMP/USDT", "20210601-20211231"),
        ("SampleStrategy", "ADA/USDT", "20210601-20211231"),
        ("NASOSv4", "ADA/USDT", "20210601-20211231"),
        pytest.param(
            "LookaheadStrategy",
            "COMP/USDT",
            "20210601-20211231",
            marks=pytest.mark.xfail(raises=LookaheadBiasException),
        ),
        pytest.param(
            "LookaheadStrategy",
            "ADA/USDT",
            "20210601-20211231",
            marks=pytest.mark.xfail(raises=LookaheadBiasException),
        ),
    ],
)
def test_buy_signals_for_lookahead_bias(strategy, pair, timerange):
    no_of_signals_to_check = 10
    CONFIG["strategy"] = strategy
    time_range = TimeRange.parse_timerange(timerange)
    candles = load_pair_history(
        datadir=USER_DATA / "data" / CONFIG["exchange"]["name"],
        timeframe=CONFIG["timeframe"],
        timerange=time_range,
        pair=pair,
        data_format="jsongz",
    )

    strategy = StrategyResolver.load_strategy(CONFIG)
    strategy.dp = DataProvider(CONFIG, Exchange(CONFIG), None)

    df = strategy.analyze_ticker(candles, {"pair": pair})

    last_buy_signals = df[df["buy"] == 1][["date"]].tail(no_of_signals_to_check).copy()

    assert len(last_buy_signals) == no_of_signals_to_check

    for idx, signal in last_buy_signals.iterrows():
        # 1000 because that's the number of candles we typically get in live trading
        assert idx > 1000  # type: ignore

        # Check that the dates match
        assert df.iloc[idx].date == signal.date  # type: ignore

        # Get the slice of the dataframe that generated the signal
        signal_df = df.iloc[idx - 999 : idx + 1].copy()  # type: ignore
        signal_df = signal_df[["date", "open", "high", "low", "close", "volume"]]

        # Reapply the strategy on the signal slice
        signal_df = strategy.analyze_ticker(signal_df, {"pair": pair})

        new_signal = signal_df[signal_df["date"] == signal.date]

        # Check that the signal is still a buy signal
        if new_signal.iloc[0].buy != 1:
            raise LookaheadBiasException(
                f"Strategy {strategy} failed to generate a buy at {signal.date}. Lookahead bias?"
            )
