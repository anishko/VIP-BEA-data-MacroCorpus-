"""Statistical profile of each series: the properties the project compares
across countries (length, missingness, persistence, volatility,
seasonality, structural breaks).

Everything is computed on the *transformed* series named in the config
(e.g. log-differences for price levels), so numbers are comparable across
series with different units.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = {"A": 1, "Q": 4, "M": 12}
PANDAS_FREQ = {"A": "YS", "Q": "QS", "M": "MS"}


def transform(values: pd.Series, how: str) -> pd.Series:
    """Apply an econometric transformation. Growth rates are in percent."""
    how = (how or "none").lower()
    if how == "none":
        return values
    if how == "diff":
        return values.diff()
    if how == "log_diff":
        return 100 * np.log(values.where(values > 0)).diff()
    if how == "pct_change":
        return 100 * values.pct_change(fill_method=None)
    raise ValueError(f"Unknown transform: {how}")


def autocorr(x: pd.Series, lag: int = 1) -> float:
    x = x.dropna()
    if len(x) <= lag + 2:
        return np.nan
    return float(x.autocorr(lag))


def seasonality_strength(x: pd.Series, freq: str) -> float:
    """Share of variance explained by period-of-year means (0 = none, 1 = all).

    Near 0 for properly seasonally adjusted data; clearly positive for NSA data.
    """
    if freq not in ("Q", "M"):
        return np.nan
    x = x.dropna()
    if len(x) < 3 * PERIODS_PER_YEAR[freq]:
        return np.nan
    season = x.index.month
    total = ((x - x.mean()) ** 2).sum()
    if total == 0:
        return np.nan
    between = x.groupby(season).transform("mean")
    return float(((between - x.mean()) ** 2).sum() / total)


def max_mean_shift(x: pd.Series, trim: float = 0.15) -> tuple[float, pd.Timestamp | None]:
    """Heuristic break detector: the split point with the largest t-stat for a
    difference in means, searched over the middle (1 - 2*trim) of the sample.

    Returns (t_stat, date). Large values (say > 5) flag a likely level shift
    worth inspecting; this is a screening tool, not a formal test.
    """
    x = x.dropna()
    n = len(x)
    lo, hi = max(int(n * trim), 2), min(int(n * (1 - trim)), n - 2)
    if hi - lo < 1:
        return np.nan, None
    vals = x.to_numpy()
    best_t, best_i = 0.0, None
    for i in range(lo, hi):
        a, b = vals[:i], vals[i:]
        se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        if se > 0:
            t = abs(a.mean() - b.mean()) / se
            if t > best_t:
                best_t, best_i = t, i
    return float(best_t), (x.index[best_i] if best_i is not None else None)


def profile_series(level: pd.Series, freq: str, how: str) -> dict:
    """`level` is the published series indexed by date."""
    level = level.sort_index()
    observed = level.dropna()
    if observed.empty:
        return {"n_obs": 0}

    # Missingness: gaps inside the observed span, on the series' own calendar.
    full_index = pd.date_range(observed.index.min(), observed.index.max(), freq=PANDAS_FREQ[freq])
    level_full = level.reindex(full_index)
    internal_missing = float(level_full.isna().mean())

    x = transform(level_full, how)
    phi = autocorr(x, 1)
    half_life = np.log(0.5) / np.log(phi) if 0 < phi < 1 else np.nan
    shift_t, shift_date = max_mean_shift(x)

    return {
        "n_obs": int(observed.size),
        "years": round(observed.size / PERIODS_PER_YEAR[freq], 1),
        "start": observed.index.min().date(),
        "end": observed.index.max().date(),
        "missing_frac": round(internal_missing, 4),
        "mean": x.mean(),
        "std": x.std(),  # volatility of the transformed series
        "acf1": phi,  # persistence
        "acf_seasonal": autocorr(x, PERIODS_PER_YEAR[freq]) if freq != "A" else np.nan,
        "half_life_periods": half_life,
        "seasonality_strength": seasonality_strength(x, freq),
        "max_mean_shift_t": shift_t,
        "max_mean_shift_date": shift_date.date() if shift_date is not None else None,
    }


def profile_corpus(obs: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, m in meta.iterrows():
        s = obs.loc[obs["series_id"] == m["series_id"]].set_index("date")["value"]
        s.index = pd.to_datetime(s.index)
        stats = profile_series(s, m["frequency"], m["transform"])
        rows.append({"series_id": m["series_id"], "name": m["name"], "geo": m["geo"],
                     "frequency": m["frequency"], "transform": m["transform"], **stats})
    out = pd.DataFrame(rows)
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(4)
    return out
