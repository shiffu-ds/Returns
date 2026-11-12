# tests for src/returns.py, mostly small cases I worked out by hand

import math

import numpy as np
import pandas as pd
import pytest

from returns import (
    annualized_return,
    annualized_vol,
    check_time_aggregation,
    drawdown,
    gross_return,
    log_returns,
    log_to_simple,
    max_drawdown,
    periods_per_year,
    simple_returns,
    simple_to_log,
)

# The roadmap's first hand exercise: the path 100 -> 110 -> 99.
PATH = pd.Series([100.0, 110.0, 99.0],
                 index=pd.date_range("2026-01-05", periods=3, freq="B"))


def test_simple_returns_hand_path():
    np.testing.assert_allclose(simple_returns(PATH).values, [0.10, -0.10])


def test_log_returns_hand_path():
    np.testing.assert_allclose(log_returns(PATH).values, [math.log(1.1), math.log(0.9)])


def test_sum_of_log_returns_equals_log_gross_return():
    assert log_returns(PATH).sum() == pytest.approx(math.log(99 / 100), abs=1e-15)


def test_product_of_gross_simple_returns_equals_total_return():
    assert (1 + simple_returns(PATH)).prod() - 1 == pytest.approx(-0.01, abs=1e-15)


def test_simple_returns_do_not_add_over_time():
    # +10% then -10% sums to 0, but you actually lost 1%.
    assert simple_returns(PATH).sum() == pytest.approx(0.0, abs=1e-15)
    assert gross_return(PATH) - 1 == pytest.approx(-0.01)


def test_minus_50_needs_plus_100_to_recover():
    p = pd.Series([100.0, 50.0, 100.0])
    np.testing.assert_allclose(simple_returns(p).values, [-0.5, 1.0])
    assert log_returns(p).sum() == pytest.approx(0.0, abs=1e-15)


def test_log_simple_round_trip():
    R = pd.Series([-0.5, -0.01, 0.0, 0.003, 0.25, 1.0])
    np.testing.assert_allclose(log_to_simple(simple_to_log(R)), R, atol=1e-15)
    np.testing.assert_allclose(simple_to_log(R), np.log(1 + R))


def test_check_time_aggregation_on_random_walk():
    rng = np.random.default_rng(0)
    p = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 2_500))))
    out = check_time_aggregation(p)
    assert out["log_gap"] < 1e-10
    assert out["simple_gap"] < 1e-10


def test_simple_returns_aggregate_across_assets_log_returns_do_not():
    # Two assets, equal weights, one period: A +50%, B -50%.
    w = np.array([0.5, 0.5])
    R = np.array([0.5, -0.5])
    portfolio_simple = w @ R                          # exact: 0%
    assert portfolio_simple == pytest.approx(0.0)
    weighted_logs = w @ np.log1p(R)                   # -0.144, wrong
    assert np.expm1(weighted_logs) != pytest.approx(portfolio_simple, abs=1e-3)


def test_max_drawdown_hand_path():
    p = pd.Series([100.0, 120.0, 90.0, 130.0, 65.0, 80.0])
    assert max_drawdown(p) == pytest.approx(-0.5)
    np.testing.assert_allclose(drawdown(p).values, [0, 0, -0.25, 0, -0.5, 80 / 130 - 1])


def test_annualized_return_compounds():
    R = pd.Series([0.001] * 252)
    assert annualized_return(R, 252) == pytest.approx(1.001 ** 252 - 1)


def test_annualized_vol_scales_with_sqrt_time():
    r = pd.Series([0.01, -0.01] * 126)
    assert annualized_vol(r, 252) == pytest.approx(r.std(ddof=1) * math.sqrt(252))
    assert annualized_vol(pd.Series([0.002] * 10)) == pytest.approx(0.0, abs=1e-15)


def test_periods_per_year_detects_calendar():
    business = pd.bdate_range("2020-01-01", "2024-12-31")
    every_day = pd.date_range("2020-01-01", "2024-12-31", freq="D")
    assert 255 < periods_per_year(business) < 265      # weekdays
    assert periods_per_year(every_day) == pytest.approx(365.25, rel=1e-3)  # crypto
