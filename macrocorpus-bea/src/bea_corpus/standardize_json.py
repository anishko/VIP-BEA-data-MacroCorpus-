"""Turn a raw BEA GetData response (any of the 12 datasets) into standard JSON series.

Every BEA dataset returns a flat list of rows. Each row has:
  - some "dimension" columns that say WHICH series it belongs to
    (NIPA: TableName/LineNumber/SeriesCode, Regional: Code/GeoFips, ITA: Indicator/AreaOrCountry/...)
  - some time column(s)   (TimePeriod like 2024Q3, or Year + Quarter for GDPbyIndustry)
  - the number            (DataValue, as text with commas and codes like "(D)")
  - unit info             (CL_UNIT, UNIT_MULT)

So the same recipe works for all of them: group rows by their dimension columns,
sort by date, and write one JSON record per group. No per-dataset parsing code needed;
anything new BEA adds is picked up automatically.

Output record (see schema/series.schema.json and docs/json_format.md):
{"series_id", "source", "country", "dataset", "table", "table_title", "title",
 "frequency", "unit", "unit_multiplier", "metric", "dimensions",
 "start", "end", "n_obs", "n_missing", "missing_codes", "retrieved", "request",
 "dates": [...], "values": [...]}
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from datetime import date

SCHEMA_VERSION = "0.1"

TIME_COLS = {"TimePeriod", "Year", "Quarter"}
# Columns that describe the number, not which series it is.
NOT_DIMENSIONS = TIME_COLS | {"DataValue", "NoteRef", "CL_UNIT", "UNIT_MULT",
                              "METRIC_NAME", "Metric_Name", "UnitOfMeasure"}
# BEA's codes for "no number here". (*) = nonzero but rounds to 0 (MNE).
MISSING_CODES = {"", "(NA)", "(D)", "(NM)", "(L)", "(X)", "(S)", "(*)", "---", "n.a.", "n.s.", "NA"}

_PERIOD = re.compile(r"^(\d{4})(?:([QMA])(\d{1,2}))?$")
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4}


# ---------- small parsers ----------

def parse_number(raw) -> tuple[float | None, str | None]:
    """Return (value, missing_code). '1,234.5' -> (1234.5, None); '(D)' -> (None, '(D)')."""
    if raw is None:
        return None, ""
    s = str(raw).strip()
    if s in MISSING_CODES:
        return None, s
    try:
        return float(s.replace(",", "")), None
    except ValueError:
        return None, s


def parse_time(row: dict) -> tuple[str, str] | None:
    """Return (ISO date of period start, frequency A/Q/M), or None if unreadable."""
    tp = row.get("TimePeriod")
    if tp:
        m = _PERIOD.match(str(tp).strip())
        if m:
            year, kind, n = int(m.group(1)), m.group(2), m.group(3)
            if kind in (None, "A"):
                return f"{year}-01-01", "A"
            n = int(n)
            if kind == "Q" and 1 <= n <= 4:
                return f"{year}-{3 * (n - 1) + 1:02d}-01", "Q"
            if kind == "M" and 1 <= n <= 12:
                return f"{year}-{n:02d}-01", "M"
        return None
    # GDPbyIndustry style: Year + Quarter ("I".."IV", or the year itself for annual rows)
    year = str(row.get("Year", "")).strip()
    if not year.isdigit():
        return None
    q = str(row.get("Quarter", "")).strip().upper()
    qn = _ROMAN.get(q) or (int(q) if q.isdigit() and 1 <= int(q) <= 4 else None)
    if qn:
        return f"{year}-{3 * (qn - 1) + 1:02d}-01", "Q"
    return f"{year}-01-01", "A"


def _is_label(col: str) -> bool:
    c = col.lower()
    return "desc" in c or "name" in c or c == "title"


def _slug(x) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(x)).strip("_")


def _unit_mult(raw) -> int:
    try:
        return int(float(str(raw).replace(",", "")))
    except (TypeError, ValueError):
        return 0


# ---------- main ----------

def dimension_columns(rows: list[dict], results: dict) -> list[str]:
    cols: list[str] = []
    for r in rows[:2000]:
        for k in r:
            if k not in cols:
                cols.append(k)
    # BEA lists its columns in Results.Dimensions; IsValue=1 means "this is a number column".
    value_cols = {d.get("Name") for d in results.get("Dimensions", []) or []
                  if isinstance(d, dict) and str(d.get("IsValue")) == "1"}
    return [c for c in cols if c not in NOT_DIMENSIONS and c not in value_cols]


def to_series(results: dict, dataset: str, table: str, request: dict | None = None,
              retrieved: date | None = None) -> tuple[list[dict], dict]:
    """Convert one GetData `Results` object into a list of standard series records.

    Returns (records, stats) where stats counts rows, dropped rows and duplicates.
    """
    rows = results.get("Data") or []
    if isinstance(rows, dict):
        rows = [rows]
    dims = dimension_columns(rows, results)
    groups: dict[tuple, dict] = defaultdict(dict)  # (dims..., freq) -> {date: row}
    stats = Counter(rows=len(rows))

    for r in rows:
        t = parse_time(r)
        if t is None:
            stats["bad_time"] += 1
            continue
        d, freq = t
        key = tuple(str(r.get(c, "")) for c in dims) + (freq,)
        if d in groups[key]:
            stats["duplicates"] += 1
        groups[key][d] = r

    table_title = results.get("PublicTable") or results.get("Statistic") or ""
    retrieved_s = (retrieved or date.today()).isoformat()
    records, used_ids = [], set()
    for key, by_date in groups.items():
        freq = key[-1]
        dim_values = dict(zip(dims, key[:-1]))
        dates = sorted(by_date)
        values, missing = [], Counter()
        for d in dates:
            v, code = parse_number(by_date[d].get("DataValue"))
            values.append(v)
            if v is None:
                missing[code or "blank"] += 1
        first = by_date[dates[0]]
        observed = [d for d, v in zip(dates, values) if v is not None]

        code_part = ".".join(_slug(v) for c, v in dim_values.items() if not _is_label(c) and v)
        if not code_part or len(code_part) > 60:
            code_part = hashlib.sha1(repr(sorted(dim_values.items())).encode()).hexdigest()[:10]
        sid = f"bea.{dataset.lower()}.{_slug(table)}.{code_part}.{freq}"
        n = 2
        while sid in used_ids:  # extremely rare: two groups slug to the same id
            sid = f"{sid}~{n}"
            n += 1
        used_ids.add(sid)

        labels = [v for c, v in dim_values.items() if _is_label(c) and v]
        records.append({
            "schema_version": SCHEMA_VERSION,
            "series_id": sid,
            "source": "BEA",
            "country": "US",
            "dataset": dataset,
            "table": table,
            "table_title": table_title,
            "title": " | ".join(dict.fromkeys(labels)) or table_title or table,
            "frequency": freq,
            "unit": first.get("CL_UNIT") or results.get("UnitOfMeasure", ""),
            "unit_multiplier": _unit_mult(first.get("UNIT_MULT", 0)),
            "metric": first.get("METRIC_NAME") or first.get("Metric_Name") or "",
            "dimensions": dim_values,
            "start": observed[0] if observed else None,
            "end": observed[-1] if observed else None,
            "n_obs": len(observed),
            "n_missing": len(dates) - len(observed),
            "missing_codes": dict(missing),
            "retrieved": retrieved_s,
            "request": request or {},
            "dates": dates,
            "values": values,
        })
    stats["series"] = len(records)
    return records, dict(stats)


def metadata_only(record: dict) -> dict:
    """The record without its data arrays (for the index file)."""
    return {k: v for k, v in record.items() if k not in ("dates", "values")}
