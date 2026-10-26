"""Offline run of `download` over all 12 datasets with a fake BEA API.

Each fake response copies the real shape of that dataset (field names from the
BEA API User Guide, wrapping quirks from the official `beaapi` package):
  - GDPbyIndustry / UnderlyingGDPbyIndustry / InputOutput / IIP: Results is a 1-item list
  - IIP: Data sits next to Results, not inside it
  - GDPbyIndustry: no TimePeriod, uses Year + Quarter (roman numerals)
  - MNE / InputOutput: Year only
  - suppressed values like "(D)" and "n.s."
"""

import json
from pathlib import Path

import pytest

from bea_corpus import download
from bea_corpus.client import BEAClient
from bea_corpus.standardize_json import parse_time, to_series

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2015, 2025)

TABLES = {
    "NIPA": ("TableName", [{"TableName": f"T1010{i}", "Description": f"Table 1.1.{i}"} for i in range(1, 7)]),
    "NIUnderlyingDetail": ("TableName", [{"TableName": "U20305", "Description": "PCE by type"}]),
    "FixedAssets": ("TableName", [{"TableName": "FAAt101", "Description": "Fixed assets"}]),
    "GDPbyIndustry": ("TableID", [{"Key": "1", "Desc": "Value added"}, {"Key": "5", "Desc": "Shares"}]),
    "UnderlyingGDPbyIndustry": ("TableID", [{"Key": "210", "Desc": "Underlying"}]),
    "InputOutput": ("TableID", [{"Key": "56", "Desc": "Use table"}]),
    "ITA": ("Indicator", [{"Key": "BalGds", "Desc": "Balance on goods"}, {"Key": "ExpGds", "Desc": "Exports"}]),
    "IIP": ("TypeOfInvestment", [{"Key": "FinAssetsExclFinDeriv", "Desc": "Assets"}]),
    "IntlServTrade": ("TypeOfService", [{"Key": "Travel", "Desc": "Travel"}]),
    "IntlServSTA": ("Channel", [{"Key": "MOFA", "Desc": "Affiliates"}]),
    "MNE": ("SeriesID", [{"Key": "4", "Desc": "Direct investment position"}]),
    "Regional": ("TableName", [{"Key": "SQGDP9", "Desc": "Real GDP by state"},
                               {"Key": "BADTABLE", "Desc": "Always errors"}]),
}


def fake_get_data(q):
    ds = q["DatasetName"]
    wrap_list = ds in ("GDPbyIndustry", "UnderlyingGDPbyIndustry", "InputOutput", "IIP")
    if ds in ("NIPA", "NIUnderlyingDetail", "FixedAssets"):
        freqs = q.get("Frequency", "A").split(",")
        rows = []
        for line in range(1, 31):
            for f in freqs:
                periods = ([f"{y}" for y in YEARS] if f == "A" else
                           [f"{y}Q{k}" for y in YEARS for k in range(1, 5)] if f == "Q" else
                           [f"{y}M{m:02d}" for y in YEARS for m in range(1, 13)])
                rows += [{"TableName": q["TableName"], "SeriesCode": f"S{line}", "LineNumber": str(line),
                          "LineDescription": f"Line {line}", "TimePeriod": p, "METRIC_NAME": "Fisher Quantity Index",
                          "CL_UNIT": "Level", "UNIT_MULT": "0", "DataValue": f"{1000 + i:,}", "NoteRef": ""}
                         for i, p in enumerate(periods)]
        return {"Data": rows, "PublicTable": f"Table {q['TableName']}"}
    if ds in ("GDPbyIndustry", "UnderlyingGDPbyIndustry"):
        rows = [{"TableID": q["TableID"], "Frequency": "Q", "Year": str(y), "Quarter": qq, "Industry": ind,
                 "IndustrYDescription": f"Industry {ind}", "DataValue": "12.5", "NoteRef": ""}
                for ind in ("11", "21", "22") for y in YEARS for qq in ("I", "II", "III", "IV")]
        rows += [{"TableID": q["TableID"], "Frequency": "A", "Year": str(y), "Quarter": str(y), "Industry": "11",
                  "IndustrYDescription": "Industry 11", "DataValue": "(D)", "NoteRef": "(D)"} for y in YEARS]
        return {"Data": rows}
    if ds == "InputOutput":
        rows = [{"TableID": 56, "Year": str(y), "RowCode": r, "RowDescr": f"Row {r}", "RowType": "Commodity",
                 "ColCode": c, "ColDescr": f"Col {c}", "ColType": "Industry", "DataValue": "3.0", "NoteRef": ""}
                for r in ("111CA", "113FF") for c in ("211", "212") for y in YEARS]
        return {"Data": rows}
    if ds in ("ITA", "IIP"):
        rows = [{"Indicator": q.get("Indicator", ""), "TypeOfInvestment": q.get("TypeOfInvestment", ""),
                 "AreaOrCountry": "AllCountries", "Frequency": f, "Year": str(y), "TimeSeriesId": f"{f}X",
                 "TimeSeriesDescription": "Some series", "TimePeriod": f"{y}Q{k}" if f != "A" else str(y),
                 "CL_UNIT": "USD", "UNIT_MULT": "6", "DataValue": "-1,234", "NoteRef": ""}
                for f in ("A", "QSA", "QNSA") for y in YEARS for k in ((1, 2, 3, 4) if f != "A" else (0,))]
        rows = [{k: v for k, v in r.items() if v != ""} for r in rows]
        if ds == "IIP":  # Data next to Results
            return {"__iip__": True, "Data": rows}
        return {"Data": rows}
    if ds in ("IntlServTrade", "IntlServSTA"):
        rows = [{"TypeOfService": "Travel", "TradeDirection": d, "Affiliation": "AllAffiliations",
                 "AreaOrCountry": "AllCountries", "TimeSeriesId": f"TS{d}", "TimeSeriesDescription": f"Travel {d}",
                 "TimePeriod": str(y), "CL_UNIT": "USD", "UNIT_MULT": "6", "DataValue": "100", "NoteRef": ""}
                for d in ("Exports", "Imports") for y in YEARS]
        return {"Data": rows}
    if ds == "MNE":
        rows = [{"Year": str(y), "SeriesID": "4", "SeriesName": "Position", "Row": c, "ColumnParent": "",
                 "Column": "All Industries", "RowCode": c, "ColumnCode": "0000",
                 "DataValue": "n.s." if c == "XX" else "5,000", "TableScale": "Millions of Dollars"}
                for c in ("308", "309", "XX") for y in YEARS]
        return {"Data": rows}
    if ds == "Regional":
        if q["TableName"] == "BADTABLE":
            raise download.BEAError("[40] Invalid TableName")
        if q["GeoFips"] != "STATE":
            raise AssertionError("first geography tried for SQGDP9 should be STATE")
        rows = [{"Code": f"SQGDP9-{q['LineCode']}", "GeoFips": f, "GeoName": n, "TimePeriod": f"{y}Q{k}",
                 "CL_UNIT": "Millions", "UNIT_MULT": "6", "DataValue": "500,000"}
                for f, n in (("01000", "Alabama"), ("13000", "Georgia")) for y in YEARS for k in range(1, 5)]
        return {"Data": rows, "Statistic": "Real GDP"}
    raise AssertionError(ds)


def fake_request(self, query):
    m, ds = query["method"], query.get("DatasetName")
    self.last_bytes, self.last_seconds = 1000, 0.01
    req = {"RequestParam": [{"ParameterName": "USERID", "ParameterValue": self.api_key}]}
    if m == "GetParameterValues":
        return {"BEAAPI": {"Request": req, "Results": {"ParamValue": TABLES[ds][1]}}}
    if m == "GetParameterValuesFiltered":
        return {"BEAAPI": {"Request": req, "Results": {"ParamValue": [{"Key": "3", "Desc": "line 3"}]}}}
    if m == "GetParameterList":
        return {"BEAAPI": {"Request": req, "Results": {"Parameter": [
            {"ParameterName": "Year", "ParameterIsRequiredFlag": "1", "AllValue": "ALL"},
            {"ParameterName": "SomethingNew", "ParameterIsRequiredFlag": "1", "AllValue": "ALL"}]}}}
    if m == "GetData":
        assert query.get("SomethingNew") == "ALL", "required params should be auto-filled"
        try:
            res = fake_get_data(query)
        except download.BEAError as exc:
            return {"BEAAPI": {"Request": req, "Results": {"Error": {"APIErrorCode": "40",
                                                                     "APIErrorDescription": str(exc)}}}}
        if res.pop("__iip__", False):
            return {"BEAAPI": {"Request": req, "Results": [{"Dimensions": []}], "Data": res["Data"]}}
        wrap = ds in ("GDPbyIndustry", "UnderlyingGDPbyIndustry", "InputOutput", "IIP")
        return {"BEAAPI": {"Request": req, "Results": [res] if wrap else res}}
    raise AssertionError(m)


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "secret-test-key")
    monkeypatch.setattr(BEAClient, "_request", fake_request)
    monkeypatch.setattr(download.time, "sleep", lambda s: None)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "datasets.yaml").write_text((ROOT / "config" / "datasets.yaml").read_text())
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_download_all_twelve(workdir):
    summaries = download.run(client=BEAClient(cache_dir="data/raw/cache", min_interval=0))
    by = {s["dataset"]: s for s in summaries}
    assert len(by) == 12
    for name, s in by.items():
        assert s["series"] > 0, f"{name} produced no series: {s['errors']}"
        lines = Path(f"data/standardized/{name}.jsonl").read_text().splitlines()
        assert len(lines) == s["series"]
        rec = json.loads(lines[0])
        assert rec["source"] == "BEA" and rec["dataset"] == name
        assert len(rec["dates"]) == len(rec["values"]) and rec["frequency"] in "AQM"
        assert rec["dates"] == sorted(rec["dates"])
    # Regional: bad table logged as a failure, good one ok; the run keeps going.
    assert by["Regional"]["failed"] == 1 and by["Regional"]["ok"] == 1
    # NIPA stops at the 300-series target (30 lines x 3 freqs = 90 per table -> 4 tables).
    assert by["NIPA"]["series"] >= 300 and by["NIPA"]["ok"] == 4
    assert Path("reports/download_summary.md").exists() and Path("reports/download_log.csv").exists()
    # The API key never ends up on disk.
    assert not any("secret-test-key" in p.read_text() for p in Path("data").rglob("*.json*"))


def test_quirky_shapes(workdir):
    download.run(only=["GDPbyIndustry", "IIP", "MNE"], client=BEAClient(cache_dir=None, min_interval=0))
    gdp = [json.loads(l) for l in Path("data/standardized/GDPbyIndustry.jsonl").read_text().splitlines()]
    freqs = {r["frequency"] for r in gdp}
    assert freqs == {"A", "Q"}
    annual = next(r for r in gdp if r["frequency"] == "A")
    assert annual["n_obs"] == 0 and annual["missing_codes"] == {"(D)": 10}
    iip = [json.loads(l) for l in Path("data/standardized/IIP.jsonl").read_text().splitlines()]
    assert {r["frequency"] for r in iip} == {"A", "Q"} and iip[0]["unit_multiplier"] == 6
    mne = [json.loads(l) for l in Path("data/standardized/MNE.jsonl").read_text().splitlines()]
    assert any(r["missing_codes"].get("n.s.") == 10 for r in mne)


def test_restandardize_matches(workdir):
    download.run(only=["NIPA", "ITA"], client=BEAClient(cache_dir=None, min_interval=0))
    before = Path("data/standardized/ITA.jsonl").read_text()
    download.restandardize()
    assert Path("data/standardized/ITA.jsonl").read_text() == before


def test_parse_time():
    assert parse_time({"TimePeriod": "2024Q3"}) == ("2024-07-01", "Q")
    assert parse_time({"TimePeriod": "2024M07"}) == ("2024-07-01", "M")
    assert parse_time({"TimePeriod": "2024M7"}) == ("2024-07-01", "M")
    assert parse_time({"TimePeriod": "2024"}) == ("2024-01-01", "A")
    assert parse_time({"Year": "2020", "Quarter": "III"}) == ("2020-07-01", "Q")
    assert parse_time({"Year": "2020", "Quarter": "2020"}) == ("2020-01-01", "A")
    assert parse_time({"Year": "2020"}) == ("2020-01-01", "A")
    assert parse_time({"TimePeriod": "garbage"}) is None


def test_single_row_dict():
    recs, _ = to_series({"Data": {"GeoFips": "1", "TimePeriod": "2020", "DataValue": "5"}}, "Regional", "X")
    assert len(recs) == 1 and recs[0]["values"] == [5.0]


def test_pick_evenly():
    assert download.pick_evenly(list(range(10)), 3) == [0, 4, 9]  # round(4.5) -> 4 (banker's rounding)
    assert download.pick_evenly([1, 2], 5) == [1, 2]


@pytest.mark.parametrize("weird", [{"Key": "3", "Desc": "x"}, [], ["3"], [{}], None])
def test_regional_line_lookup_never_crashes(weird, monkeypatch):
    monkeypatch.setenv("BEA_API_KEY", "k")
    client = BEAClient(cache_dir=None, min_interval=0)
    monkeypatch.setattr(client, "get_parameter_values_filtered", lambda *a, **k: weird)
    attempts = download._attempts(client, "Regional", "TableName", "CAINC5N", {"Year": "ALL"})
    assert attempts and all(a["LineCode"] for a in attempts)
