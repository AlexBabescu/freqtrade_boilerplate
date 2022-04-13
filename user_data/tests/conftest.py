from pathlib import Path
import pytest
from freqtrade.configuration import TimeRange
from freqtrade.configuration import Configuration

user_data = Path(__file__).parent.parent


def pytest_configure():
    pytest.user_data = user_data
    pytest.config = Configuration.from_files(
        [
            str(user_data / "configs" / "config-usdt-binance.json"),
            str(user_data / "configs" / "pairlist-static-usdt-binance.json"),
        ]
    )
    pytest.data_timerange = TimeRange.parse_timerange("20210101-20211231")
