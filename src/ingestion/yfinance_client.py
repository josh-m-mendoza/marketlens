## two functions
# fetch_price_history(ticker, period, interval)
# fetch_and_store(tickers, period, interval)

# fetch_price_history(ticker, period, interval)
from src.storage.db import upsert_prices
import yfinance as yf

def fetch_price_history(ticker, period="2y", interval="1d"):
    # call the API and fail loudly if nothing comes back (empty DataFrame)
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data returned for '{ticker}' (period = {period}, interval = {interval})")
    return df

def fetch_and_store(tickers, period="2y", interval="1d"):
    # loops over list of tickers
    # calls fetch_price_history for each one
    # hands each result straight into upsert_prices
    # skips a failing ticker and reports failed ones
    successes = {} # ticker rows written
    failures = {} #ticker and msg
    for tickr in tickers:
        try:
            df = fetch_price_history(tickr, period, interval)
            successes[tickr] = upsert_prices(df,tickr)
        except ValueError as e:
            failures[tickr] = str(e)

    return {"successes": successes, "failures": failures}