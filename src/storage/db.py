# Four peices needed
# Open a connection
# Somethiing to run schema.sql once
# Something to write rows in
# Something to read rows back out as a Data Frame

import sqlite3
import pandas as pd
from config import DB_PATH
from pathlib import Path

# get_connection() - opens (or creates if non-existent) SQL file at DB_PATH
def get_connection():
    # Open connection; creates a file if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn

# init_db() - calls get_connection(), runs schema.sql 

def init_db():
    conn = get_connection()
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, 'r') as file:
        sql_script = file.read()

    conn.executescript(sql_script)

    conn.commit()
    conn.close()
    return

# upsert_prices(df, ticker) - calls get_connection(), reshapes incoming DataFrame (df) to match table's columns
# runs insert ... on conflict ... do update for each row
# what ingestion module (yfinance_client.py) will call after it fetches data

def upsert_prices(df, ticker):
    # get connection -– only necessary for the write portion
    conn = get_connection()

    # reshape first
    # convert date from index to column
    df = df.reset_index()

    # convert the date to YYYY-MM-DD
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    #rename columns
    df = df.rename(columns = {"Date":"date",
                         "Open":"open", 
                         "High":"high",
                         "Low":"low",
                         "Close":"close",
                         "Volume":"volume"})

    # assign ticker column
    df['ticker'] = ticker

    # reorder columns
    df = df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']]

    # write second
    # get reshaped rows into form executemany can use
    records = df.to_records(index=False).tolist()

    # write actual upsert SQL
    sql = """INSERT INTO prices (ticker, date, open, high, low, close, volume)
    VALUES (?,?,?,?,?,?,?)
    ON CONFLICT(ticker, date) DO UPDATE SET
    open = excluded.open,
    high = excluded.high,
    low = excluded.low,
    close = excluded.close,
    volume = excluded.volume"""
    # run and clean
    conn.executemany(sql, records)
    conn.commit() # let changes persist
    conn.close()

    return len(records)

# load_prices(ticker, start=None, end=None),
# calls get_connection(), builds a SELECT (optionally narrowes by data range), runs it throuhg pd.read_sql_query
# shapes result back into DataFrame indexed by date.

def load_prices(ticker, start=None, end=None):

    # get a connection
    conn = get_connection()

    # build a SELECT stmt
    # only ticker, no date range
    sql = f"""
    SELECT * FROM prices
    WHERE ticker = ?
    """
    params = [ticker]
    # start provided
    if start is not None:
        sql += " AND date >= ?"
        params.append(start)
    if end is not None:
        sql += " AND date <= ?"
        params.append(end)

    # read sql query

    df = pd.read_sql_query(sql, 
                                     conn, 
                                     params=params,
                                     index_col='date',
                                     parse_dates=['date'])
    conn.close()
    return df

if __name__ == "__main__":
    init_db()