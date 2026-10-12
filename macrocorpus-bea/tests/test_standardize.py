"""Tests run offline against payloads shaped like real BEA responses
(field names and layout follow the BEA API User Guide examples)."""

import numpy as np
import pandas as pd
import pytest

from bea_corpus.client import BEAError, extract_results
from bea_corpus.standardize import SeriesSpec, parse_period, parse_value, standardize


def nipa_payload():
    rows = []
    for line, desc, base in [("1", "Personal consumption expenditures (PCE)", 100.0),
                             ("25", "PCE excluding food and energy", 90.0)]:
        for i, tp in enumerate(["2023M11", "2023M12", "2024M1", "2024M2"]):
            rows.append({"TableName": "T20804", "SeriesCode": f"S{line}", "LineNumber": line,
                         "LineDescription": desc, "TimePeriod": tp, "METRIC_NAME": "Fisher Price Index",
                         "CL_UNIT": "Level", "UNIT_MULT": "0", "DataValue": f"{base + i:,.3f}", "NoteRef": "T20804"})
    rows[2]["DataValue"] = "(NA)"
    return {"BEAAPI": {"Request": {}, "Results": {"Statistic": "NIPA Table", "Data": rows, "Notes": []}}}


def regional_payload():
    rows = []
    for fips, name in [("00000", "United States"), ("13000", "Georgia")]:
        for i, tp in enumerate(["2024Q1", "2024Q2", "2024Q3"]):
            rows.append({"Code": "SQGDP9-1", "GeoFips": fips, "GeoName": name, "TimePeriod": tp,
                         "CL_UNIT": "Millions of chained 2017 dollars", "UNIT_MULT": "6",
                         "DataValue": f"{1_000_000 * (1 + i / 100):,.0f}"})
    return {"BEAAPI": {"Request": {}, "Results": {"Statistic": "Real GDP", "UnitOfMeasure": "Millions", "Data": rows}}}


def ita_payload():
    rows = [{"Indicator": "BalGds", "AreaOrCountry": "AllCountries", "Frequency": "QSA", "Year": "2024",
             "TimeSeriesId": "BalGds", "TimeSeriesDescription": "Balance on goods", "TimePeriod": f"2024Q{q}",
             "CL_UNIT": "USD", "UNIT_MULT": "6", "DataValue": str(-270000 - q)} for q in (1, 2, 3)]
    return {"BEAAPI": {"Request": {}, "Results": [{"Data": rows}]}}  # list-wrapped, as ITA does


def test_parse_period():
    assert parse_period("2024") == (pd.Timestamp("2024-01-01"), "A")
    assert parse_period("2024Q3") == (pd.Timestamp("2024-07-01"), "Q")
    assert parse_period("2024M7") == (pd.Timestamp("2024-07-01"), "M")
    assert parse_period("2024M07") == (pd.Timestamp("2024-07-01"), "M")
    with pytest.raises(ValueError):
        parse_period("Q3-2024")


def test_parse_value():
    assert parse_value("1,234.5") == 1234.5
    assert parse_value("-270,001") == -270001
    assert np.isnan(parse_value("(NA)"))
    assert np.isnan(parse_value(""))


def test_nipa_select_by_line():
    spec = SeriesSpec(id="pce", dataset="NIPA", params={"TableName": "T20804"}, select={"line": 1})
    obs, meta = standardize(extract_results(nipa_payload()), spec)
    assert list(obs["series_id"].unique()) == ["pce"]
    assert len(obs) == 4 and obs["value"].isna().sum() == 1
    assert meta.iloc[0]["frequency"] == "M"
    assert meta.iloc[0]["n_obs"] == 3


def test_nipa_select_by_match():
    spec = SeriesSpec(id="core", dataset="NIPA", params={"TableName": "T20804"},
                      select={"match": "excluding food and energy"})
    obs, meta = standardize(extract_results(nipa_payload()), spec)
    assert meta.iloc[0]["line"] == "25"
    assert obs["value"].iloc[0] == 90.0


def test_regional_splits_by_geography():
    spec = SeriesSpec(id="state_gdp", dataset="Regional", params={"TableName": "SQGDP9", "LineCode": 1})
    obs, meta = standardize(extract_results(regional_payload()), spec)
    assert set(meta["series_id"]) == {"state_gdp.00000", "state_gdp.13000"}
    assert set(meta["geo"]) == {"United States", "Georgia"}
    assert (meta["unit_mult"] == 6).all()
    assert obs["value"].max() == 1_020_000


def test_ita_list_wrapped_results():
    spec = SeriesSpec(id="bal", dataset="ITA", params={"Indicator": "BalGds"})
    obs, meta = standardize(extract_results(ita_payload()), spec)
    assert meta.iloc[0]["series_id"] == "bal"
    assert meta.iloc[0]["frequency"] == "Q"
    assert obs["value"].tolist() == [-270001, -270002, -270003]


def test_api_error_raises():
    payload = {"BEAAPI": {"Request": {}, "Results": {"Error": {
        "APIErrorCode": "1", "APIErrorDescription": "Invalid Request - Invalid API UserId."}}}}
    with pytest.raises(BEAError, match="Invalid API UserId"):
        extract_results(payload)


def test_empty_selection_raises():
    spec = SeriesSpec(id="x", dataset="NIPA", params={}, select={"line": 999})
    with pytest.raises(ValueError, match="matched no rows"):
        standardize(extract_results(nipa_payload()), spec)
