# Download + cache price data and keep a manifest of every raw file.
# yfinance data goes to data/raw/yfinance, stooq csvs (downloaded by hand) go to data/raw/stooq

import hashlib
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
MANIFEST = os.path.join(ROOT, "data", "MANIFEST.csv")


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def add_to_manifest(source, symbol, path, url, df):
    row = {
        "source": source,
        "symbol": symbol,
        "file": os.path.relpath(path, ROOT),
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rows": len(df),
        "first_date": df.index.min().date(),
        "last_date": df.index.max().date(),
        "sha256": file_hash(path),
    }
    if os.path.exists(MANIFEST):
        m = pd.read_csv(MANIFEST)
        m = m[m["file"] != row["file"]]  # replace old entry for the same file
        m = pd.concat([m, pd.DataFrame([row])])
    else:
        m = pd.DataFrame([row])
    m.sort_values(["source", "symbol"]).to_csv(MANIFEST, index=False)


def get_data(ticker, start, end, refresh=False):
    """Daily data from yfinance. Uses the cached csv if it's already there."""
    fname = ticker.replace("^", "").replace("=", "_").replace(".", "_") + ".csv"
    path = os.path.join(RAW_DIR, "yfinance", fname)

    if os.path.exists(path) and not refresh:
        return pd.read_csv(path, index_col=0, parse_dates=True)

    # auto_adjust=False so I get both Close and Adj Close
    df = yf.download(ticker, start=start, end=end, auto_adjust=False,
                     actions=True, progress=False, multi_level_index=False)
    if len(df) == 0:
        raise ValueError(f"no data for {ticker}")
    df.index = df.index.tz_localize(None)
    df.index.name = "Date"

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path)
    add_to_manifest("yfinance", ticker, path,
                    f"https://finance.yahoo.com/quote/{ticker}/history (yfinance {yf.__version__})", df)
    return df


def load_stooq(symbol):
    """Stooq blocks scripted downloads (js browser check), so I download the csv
    in the browser and save it in data/raw/stooq/. Returns None if not there yet."""
    folder = os.path.join(RAW_DIR, "stooq")
    for name in [symbol.replace(".", "_") + "_d.csv", symbol + ".csv"]:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            add_to_manifest("stooq", symbol, path, f"https://stooq.com/q/d/?s={symbol} (manual download)", df)
            return df
    return None
