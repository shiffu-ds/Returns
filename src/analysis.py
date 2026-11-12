# Data loading, cleaning and the numbers shown in the app.
# Cleaning rules are the same ones worked out in notebooks/01_returns.ipynb.

import numpy as np
import pandas as pd

import returns as rt
from data import MANIFEST, get_data

START, END = "2016-11-01", "2026-11-01"

# name -> (yahoo ticker, description, currency)
ASSETS = {
    "SPY": ("SPY", "S&P 500 ETF", "USD"),
    "EFA": ("EFA", "Developed markets ex-US ETF", "USD"),
    "EEM": ("EEM", "Emerging markets ETF", "USD"),
    "TLT": ("TLT", "20+ year US Treasury ETF", "USD"),
    "GLD": ("GLD", "Gold ETF", "USD"),
    "AAPL": ("AAPL", "Apple", "USD"),
    "NVDA": ("NVDA", "NVIDIA", "USD"),
    "BTC": ("BTC-USD", "Bitcoin", "USD"),
    "OGDC": ("OGDC.KA", "Oil & Gas Development Co. (PSX)", "PKR"),
    "USDPKR": ("PKR=X", "US dollar in Pakistani rupees", "PKR"),
}
USD_ASSETS = [k for k, v in ASSETS.items() if v[2] == "USD"]
PERIODS = {"1Y": 1, "3Y": 3, "5Y": 5, "10Y": 10}


def remove_spikes(s, thresh=0.015):
    """Drop quotes more than 1.5% away from the centered 5-day median (used for FX)."""
    s = s.dropna()
    removed = []
    for _ in range(3):
        med = s.rolling(5, center=True, min_periods=3).median()
        bad = np.abs(np.log(s / med)) > thresh
        removed.append(s[bad])
        s = s[~bad]
    return s, pd.concat(removed).sort_index()


def clean(df, col="Adj Close"):
    """Returns (clean prices, removed points)."""
    p = df[col]
    if (df["Volume"] > 0).mean() > 0.5:
        # exchange traded: zero volume = market closed, yahoo repeats the old price
        keep = df["Volume"] > 0
        return p[keep].dropna(), p[~keep]
    # FX has no volume and its open/high/low are unreliable -> spike filter on the close
    return remove_spikes(p)


def load_all():
    raw, prices, removed = {}, {}, {}
    for name, (ticker, _, _) in ASSETS.items():
        raw[name] = get_data(ticker, START, END)
        prices[name], removed[name] = clean(raw[name])
    return raw, prices, removed


def last_download():
    m = pd.read_csv(MANIFEST)
    return m["retrieved_utc"].max()[:10]


def window(p, period):
    years = PERIODS[period]
    return p.loc[p.index[-1] - pd.DateOffset(years=years):]


def stats(p):
    R = rt.simple_returns(p)
    r = rt.log_returns(p)
    ppy = rt.periods_per_year(p.index)
    return {
        "total": p.iloc[-1] / p.iloc[0] - 1,
        "cagr": rt.annualized_return(R, ppy),
        "vol": rt.annualized_vol(r, ppy),
        "mdd": rt.max_drawdown(p),
        "worst": R.min(),
        "best": R.max(),
        "ppy": ppy,
    }


# tables below return plain numbers (percent columns already x100) so the
# dashboard can sort them and format them itself

def stats_table(prices, names, period):
    rows = []
    for name in names:
        s = stats(window(prices[name], period))
        rows.append({
            "Asset": name,
            "Description": ASSETS[name][1],
            "Total return": s["total"] * 100,
            "Annual return": s["cagr"] * 100,
            "Annual volatility": s["vol"] * 100,
            "Max drawdown": s["mdd"] * 100,
            "Worst day": s["worst"] * 100,
            "Best day": s["best"] * 100,
            "Days / year": round(s["ppy"]),
        })
    return pd.DataFrame(rows)


def identity_table(prices, period):
    rows = []
    for name, p in prices.items():
        c = rt.check_time_aggregation(window(p, period))
        rows.append({
            "Asset": name,
            "Σ log returns": c["sum_log"],
            "ln(P_T / P_0)": c["log_gross"],
            "Gap": c["log_gap"],
            "Passes": bool(c["log_gap"] < 1e-10),
            "Σ simple returns (wrong)": c["sum_simple"] * 100,
            "Real total return": c["total_simple"] * 100,
        })
    return pd.DataFrame(rows)


def portfolio(prices, a, b, w, period):
    """Daily rebalanced 2-asset portfolio: correct (weights on simple returns)
    vs the common mistake (weights on log returns)."""
    Ra = rt.simple_returns(window(prices[a], period))
    Rb = rt.simple_returns(window(prices[b], period))
    common = Ra.index.intersection(Rb.index)
    Ra, Rb = Ra[common], Rb[common]
    exact = w * Ra + (1 - w) * Rb
    wrong = np.expm1(w * np.log1p(Ra) + (1 - w) * np.log1p(Rb))
    return (1 + exact).cumprod(), (1 + wrong).cumprod()


def ogdc_in_usd(prices, period):
    pkr = window(prices["OGDC"], period)
    fx = prices["USDPKR"].reindex(pkr.index, method="ffill")   # last known rate
    usd = (pkr / fx).dropna()
    return pkr[usd.index], usd


def dividends_table(raw, prices):
    rows = []
    for name, df in raw.items():
        keep = prices[name].index
        price_ret = df["Close"][keep].iloc[-1] / df["Close"][keep].iloc[0] - 1
        total_ret = prices[name].iloc[-1] / prices[name].iloc[0] - 1
        rows.append({
            "Asset": name,
            "Price return (Close)": price_ret * 100,
            "Total return (Adj Close)": total_ret * 100,
            "From dividends (pp)": (total_ret - price_ret) * 100,
            "Dividend payments": int((df["Dividends"] > 0).sum()),
        })
    return pd.DataFrame(rows)


def unadjusted(df):
    """Undo yahoo's split adjustment to get the price that actually traded."""
    splits = df["Stock Splits"][df["Stock Splits"] > 0]
    factor = pd.Series(1.0, index=df.index)
    for date, ratio in splits.items():
        factor[df.index < date] *= ratio
    return df["Close"] * factor, splits


def quality_table(raw, prices):
    rows = []
    for name, df in raw.items():
        ret = df["Adj Close"].pct_change()
        has_vol = (df["Volume"] > 0).mean() > 0.5
        outside = (df["Close"] > df["High"] * 1.001) | (df["Close"] < df["Low"] * 0.999)
        rows.append({
            "Asset": name,
            "Rows": len(df),
            "Missing": int(df["Adj Close"].isna().sum()),
            "Zero volume": int((df["Volume"] == 0).sum()) if has_vol else None,   # FX has no volume
            "Close outside high–low": int(outside.sum()),
            "Zero-return days": int((ret == 0).sum()),
            "Moves > 10%": int((ret.abs() > 0.10).sum()),
            "Splits": int((df["Stock Splits"] > 0).sum()),
            "Rows removed": len(df) - len(prices[name]),
        })
    return pd.DataFrame(rows)
