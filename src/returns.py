# Return calculations for week 1
#   simple return  R_t = P_t / P_{t-1} - 1
#   log return     r_t = ln(P_t / P_{t-1}) = ln(1 + R_t)
# over time: sum of log returns = ln(P_T / P_0), product of (1 + R_t) = P_T / P_0

import numpy as np

TRADING_DAYS = 252


def simple_returns(prices):
    return (prices / prices.shift(1) - 1).iloc[1:]


def log_returns(prices):
    return np.log(prices / prices.shift(1)).iloc[1:]


def simple_to_log(R):
    return np.log1p(R)


def log_to_simple(r):
    return np.expm1(r)


def gross_return(prices):
    p = prices.dropna()
    return p.iloc[-1] / p.iloc[0]


def check_time_aggregation(prices):
    """Compare sum of log returns with ln(P_T/P_0), and prod(1+R) with P_T/P_0."""
    p = prices.dropna()
    R = simple_returns(p)
    r = log_returns(p)
    gross = gross_return(p)
    return {
        "n_returns": len(r),
        "sum_log": r.sum(),
        "log_gross": np.log(gross),
        "log_gap": abs(r.sum() - np.log(gross)),
        "prod_simple": (1 + R).prod(),
        "gross": gross,
        "simple_gap": abs((1 + R).prod() - gross) / gross,
        "sum_simple": R.sum(),       # this one is NOT the total return
        "total_simple": gross - 1,
    }


def periods_per_year(index):
    # stocks ~252, PSX ~246, fx ~260, crypto 365 -> don't just assume 252
    years = (index[-1] - index[0]).days / 365.25
    return (len(index) - 1) / years


def annualized_return(R, ppy=TRADING_DAYS):
    R = R.dropna()
    return (1 + R).prod() ** (ppy / len(R)) - 1


def annualized_vol(r, ppy=TRADING_DAYS):
    return r.dropna().std() * np.sqrt(ppy)


def drawdown(prices):
    return prices / prices.cummax() - 1


def max_drawdown(prices):
    return drawdown(prices.dropna()).min()
