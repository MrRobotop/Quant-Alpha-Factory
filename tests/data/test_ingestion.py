"""Tests for market data ingestion."""

from __future__ import annotations

import pandas as pd
import pytest

from src.data.ingestion import DataIngestionError, load_market_data, normalize_market_data


def test_load_market_data_csv_normalizes_columns(tmp_path) -> None:
    path = tmp_path / "prices.csv"
    path.write_text(
        "Date,Ticker,Open,High,Low,Close,Volume,Adj Close\n"
        "2024-01-03, BBB ,50,52,49,51,1000,51\n"
        "2024-01-02,AAA,10,11,9,10.5,2000,10.5\n",
        encoding="utf-8",
    )

    frame = load_market_data(path)

    assert list(frame.columns) == [
        "date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
    ]
    assert frame["symbol"].tolist() == ["AAA", "BBB"]
    assert pd.api.types.is_datetime64_any_dtype(frame["date"])


def test_load_market_data_rejects_unknown_extension(tmp_path) -> None:
    path = tmp_path / "prices.txt"
    path.write_text("date,symbol\n", encoding="utf-8")

    with pytest.raises(DataIngestionError, match="Unsupported data file extension"):
        load_market_data(path)


def test_normalize_market_data_preserves_extra_columns() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "symbol": ["AAA"],
            "open": [1],
            "high": [2],
            "low": [1],
            "close": [2],
            "volume": [100],
            "sector": ["Tech"],
        }
    )

    normalized = normalize_market_data(frame)

    assert normalized.columns.tolist()[-1] == "sector"

