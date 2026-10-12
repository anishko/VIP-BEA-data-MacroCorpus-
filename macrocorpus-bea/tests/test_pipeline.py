"""End-to-end: fetch -> standardize -> profile, with the network stubbed out."""

import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from bea_corpus import cli
from bea_corpus.client import BEAClient

ROOT = Path(__file__).resolve().parents[1]


def fake_request(self, query):
    payload = _fake_payload(query)
    # Real responses echo the request, including the UserID.
    payload["BEAAPI"]["Request"] = {"RequestParam": [{"ParameterName": "USERID", "ParameterValue": self.api_key}]}
    return payload


def _fake_payload(query):
    ds = query["DatasetName"]
    rng = np.random.default_rng(len(str(query)))
    if ds == "NIPA":
        freq = query["Frequency"]
        periods = ([f"{y}M{m}" for y in range(1990, 2025) for m in range(1, 13)] if freq == "M"
                   else [f"{y}Q{q}" for y in range(1990, 2025) for q in range(1, 5)])
        level = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.003, len(periods))))
        rows = []
        for line, desc in [("1", "Total"), ("25", "PCE excluding food and energy")]:
            rows += [{"LineNumber": line, "LineDescription": desc, "SeriesCode": "X", "TimePeriod": tp,
                      "CL_UNIT": "Level", "UNIT_MULT": "0", "DataValue": f"{v:,.3f}"}
                     for tp, v in zip(periods, level)]
        return {"BEAAPI": {"Results": {"Data": rows}}}
    if ds == "Regional":
        rows = [{"GeoFips": f, "GeoName": n, "TimePeriod": f"{y}Q{q}", "CL_UNIT": "Millions", "UNIT_MULT": "6",
                 "DataValue": f"{500_000 * (1.005 ** (4 * (y - 2005) + q)):,.0f}"}
                for f, n in [("00000", "United States"), ("13000", "Georgia")]
                for y in range(2005, 2025) for q in range(1, 5)]
        return {"BEAAPI": {"Results": {"Data": rows}}}
    if ds == "ITA":
        seasonal = query["Frequency"] == "QNSA"
        rows = [{"TimeSeriesId": "BalGds", "Frequency": query["Frequency"], "TimeSeriesDescription": "Balance on goods",
                 "TimePeriod": f"{y}Q{q}", "CL_UNIT": "USD", "UNIT_MULT": "6",
                 "DataValue": str(-200000 - 1000 * (y - 2000) + (15000 * (q - 2.5) if seasonal else 0)
                                  + rng.normal(0, 500))}
                for y in range(2000, 2025) for q in range(1, 5)]
        return {"BEAAPI": {"Results": [{"Data": rows}]}}
    raise AssertionError(ds)


def test_fetch_and_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "test-key")
    monkeypatch.setattr(BEAClient, "_request", fake_request)
    shutil.copytree(ROOT / "config", tmp_path / "config")
    monkeypatch.chdir(tmp_path)

    cli.main(["fetch"])
    meta = pd.read_csv("data/processed/series_metadata.csv")
    assert {"us_pce_price_index", "us_core_pce_price_index", "state_real_gdp.13000",
            "us_goods_balance_sa", "us_goods_balance_nsa"} <= set(meta["series_id"])
    assert not any("BEA_API_KEY" in p.read_text() or "test-key" in p.read_text()
                   for p in Path("data/raw/cache").glob("*.json"))

    cli.main(["profile"])
    prof = pd.read_csv("reports/profile.csv").set_index("series_id")
    # The NSA trade series should look far more seasonal than the SA one.
    assert prof.loc["us_goods_balance_nsa", "seasonality_strength"] > 0.5
    assert prof.loc["us_goods_balance_sa", "seasonality_strength"] < 0.3
