import pytest
from freqtrade.data.dataprovider import DataProvider
from freqtrade.data.history import load_pair_history
from freqtrade.exchange import Exchange
from freqtrade.resolvers import StrategyResolver


class LookaheadBiasException(Exception):
    pass


@pytest.mark.parametrize(
    "strategy,pair",
    [
        ("SampleStrategy", "COMP/USDT"),
        ("SampleStrategy", "ADA/USDT"),
        pytest.param(
            "LookaheadStrategy",
            "COMP/USDT",
            marks=pytest.mark.xfail(raises=LookaheadBiasException, strict=True),
        ),
        pytest.param(
            "LookaheadStrategy",
            "ADA/USDT",
            marks=pytest.mark.xfail(raises=LookaheadBiasException, strict=True),
        ),
    ],
)
def test_buy_signals_for_lookahead_bias(strategy, pair):
    no_of_signals_to_check = 10
    pytest.config["strategy"] = strategy
    candles = load_pair_history(
        datadir=pytest.user_data / "data" / pytest.config["exchange"]["name"],
        timeframe=pytest.config["timeframe"],
        timerange=pytest.data_timerange,
        pair=pair,
        data_format="jsongz",
    )

    strategy = StrategyResolver.load_strategy(pytest.config)
    strategy.dp = DataProvider(pytest.config, Exchange(pytest.config), None)

    df = strategy.analyze_ticker(candles.copy(), {"pair": pair})

    col = ["date", "enter_long"]
    if "enter_tag" in df.columns:
        col += ["enter_tag"]

    last_buy_signals = df[df["enter_long"] == 1][col].tail(no_of_signals_to_check).copy()

    assert len(last_buy_signals) == no_of_signals_to_check

    for idx, signal in last_buy_signals.iterrows():
        # 999 because that's the number of candles we typically get in live trading
        assert idx > 999  # type: ignore

        # Check that the dates match
        assert df.iloc[idx].date == signal.date  # type: ignore

        # Get the slice of the dataframe that generated the signal
        # This is equivalent to the dataframe we received from the exchange
        exchange_df = df.iloc[idx - 998 : idx + 1].copy()  # type: ignore
        exchange_df = (
            exchange_df[["date", "open", "high", "low", "close", "volume"]]
            .reset_index()
            .drop(columns=["index"])
        )

        # Reapply the strategy on the signal slice
        analyzed_df = strategy.analyze_ticker(exchange_df.copy(), {"pair": pair})

        new_signal = analyzed_df[analyzed_df["date"] == signal.date]

        # Check that the signal is still a buy signal
        if new_signal.iloc[0].enter_long != 1:
            raise LookaheadBiasException(
                f"Strategy {strategy} failed to generate a buy at {signal.date}. Lookahead bias?"
            )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
