from src.storage.db import init_db, upsert_prices, load_prices
import pandas as pd
import pytest

@pytest.fixture
def sample_price_df():
    dates = pd.date_range("2026-08-20", periods=3, tz="America/New_York")
    
    df = pd.DataFrame({"Open": [100.0, 101.0, 102.5],
                    "High": [101.5, 102.0, 103.0],
                    "Low": [99.5, 100.5, 101.5],
                    "Close": [101.0, 101.5, 102.0],
                    "Volume": [1_000_000, 1_200_000, 900_000],},
                    index=dates)
        
    df.index.name = "Date"
    return df

def test_upsert_returns_row_count(tmp_path, sample_price_df):
    db_path = tmp_path / "test.db"

    init_db(db_path)
    result = upsert_prices(df=sample_price_df, ticker="TEST", db_path=db_path)
    assert result == 3

def test_load_prices(tmp_path, sample_price_df):
    db_path = tmp_path / "test.db"
    # Arrange, Act, Assert
    # arrange database into know state 
    init_db(db_path)
    upsert_prices(ticker="TEST", df=sample_price_df, db_path=db_path)

    # act - call actual function under test
    result_df = load_prices(ticker="TEST", db_path=db_path)
    # assert
    assert len(result_df) == 3
    assert result_df.loc["2026-08-20", "close"] == 101.0
    assert isinstance(result_df.index, pd.DatetimeIndex)
