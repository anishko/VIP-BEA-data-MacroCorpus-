import numpy as np
import pandas as pd

from bea_corpus.profile import max_mean_shift, profile_series, seasonality_strength, transform


def monthly(values, start="2000-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"))


def test_transform_log_diff():
    s = monthly([100.0, 110.0, 121.0])
    out = transform(s, "log_diff")
    assert np.isnan(out.iloc[0])
    assert abs(out.iloc[1] - 100 * np.log(1.1)) < 1e-9


def test_persistent_series_has_high_acf():
    rng = np.random.default_rng(0)
    x = np.zeros(400)
    for t in range(1, 400):
        x[t] = 0.9 * x[t - 1] + rng.normal()
    prof = profile_series(monthly(x), "M", "none")
    assert prof["acf1"] > 0.8
    assert 4 < prof["half_life_periods"] < 10  # ln(.5)/ln(.9) ≈ 6.6


def test_seasonality_detects_nsa_pattern():
    rng = np.random.default_rng(1)
    months = np.tile(np.arange(12), 20)
    seasonal = monthly(10 * np.sin(2 * np.pi * months / 12) + rng.normal(size=240))
    flat = monthly(rng.normal(size=240))
    assert seasonality_strength(seasonal, "M") > 0.8
    assert seasonality_strength(flat, "M") < 0.15


def test_mean_shift_found_at_break():
    rng = np.random.default_rng(2)
    x = monthly(np.r_[rng.normal(0, 1, 150), rng.normal(5, 1, 150)])
    t, when = max_mean_shift(x)
    assert t > 20
    assert when == x.index[150]


def test_missingness_counts_internal_gaps():
    s = monthly([1.0, 2.0, np.nan, 4.0, 5.0])
    prof = profile_series(s, "M", "none")
    assert prof["n_obs"] == 4
    assert prof["missing_frac"] == 0.2
