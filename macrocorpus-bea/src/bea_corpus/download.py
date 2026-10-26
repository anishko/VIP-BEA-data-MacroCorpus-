"""Sample download across ALL BEA datasets, plus a report on how heavy each one is.

For each dataset in config/datasets.yaml:
  1. catalog : list every table/indicator the dataset offers  -> data/catalog/<Dataset>.json
  2. sample  : GetData on up to `max_calls` of them, spread across the list
               raw responses                                  -> data/raw/<Dataset>/<table>.json
  3. convert : standard JSON series (one line per series)     -> data/standardized/<Dataset>.jsonl
  4. log     : bytes, seconds, rows, series per call          -> reports/download_log.csv
               per-dataset totals + full-size estimate        -> reports/download_summary.md
"""

from __future__ import annotations

import csv
import json
import re
import time
from datetime import date
from pathlib import Path

import yaml

from .client import BEAClient, BEAError
from .standardize_json import metadata_only, to_series

DATA = Path("data")
REPORTS = Path("reports")

LOG_FIELDS = ["dataset", "table", "status", "error", "kb", "seconds", "rows", "series", "from_cache"]


# ---------- helpers ----------

def _key(v) -> str:
    if not isinstance(v, dict):
        return str(v)
    for k in ("Key", "TableName", "TableID", "TableNumber", "Code"):
        if v.get(k) not in (None, ""):
            return str(v[k])
    return str(next(iter(v.values()), ""))


def _as_list(x) -> list:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _desc(v: dict) -> str:
    for k in ("Desc", "Description", "Descr"):
        if v.get(k):
            return str(v[k])
    return ""


def pick_evenly(items: list, n: int) -> list:
    """n items spread across the list (first, ..., last) so the sample covers the whole catalog."""
    if n >= len(items):
        return list(items)
    if n <= 1:
        return items[:1]
    step = (len(items) - 1) / (n - 1)
    return [items[round(i * step)] for i in range(n)]


def _safe_name(x: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", x)[:80] or "table"


def regional_geo(table: str) -> list[str]:
    """Which geography to ask for, by Regional table prefix (with fallbacks)."""
    t = table.upper()
    if t.startswith(("MA", "MARPP")):
        return ["MSA", "STATE", "00000"]
    if t.startswith("PORT"):
        return ["PORT", "00000"]
    return ["STATE", "00000"]


def fill_required(client: BEAClient, dataset: str, params: dict, split_by: str) -> dict:
    """Add any required parameter we didn't set, using the dataset's 'all' value."""
    out = dict(params)
    try:
        plist = client.get_parameter_list(dataset)
    except BEAError:
        return out
    given = {k.lower() for k in out} | {split_by.lower()}
    for p in plist:
        name = p.get("ParameterName", "")
        required = str(p.get("ParameterIsRequiredFlag")) == "1"
        if required and name.lower() not in given and name.lower() not in ("userid", "method", "datasetname"):
            all_value = p.get("AllValue") or p.get("ParameterDefaultValue")
            if all_value:
                out[name] = all_value
    return out


# ---------- one dataset ----------

def catalog_dataset(client: BEAClient, dataset: str, split_by: str) -> list[dict]:
    values = client.get_parameter_values(dataset, split_by)
    items = [{"key": _key(v), "description": _desc(v) if isinstance(v, dict) else ""} for v in _as_list(values)]
    params = []
    try:
        params = client.get_parameter_list(dataset)
    except BEAError:
        pass
    out = DATA / "catalog" / f"{dataset}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"dataset": dataset, "split_by": split_by, "n_values": len(items),
                               "parameters": params, "values": items}, indent=1))
    return items


def download_dataset(client: BEAClient, dataset: str, cfg: dict, defaults: dict,
                     use_cache: bool = True, log=print) -> dict:
    split_by = cfg["split_by"]
    max_calls = int(cfg.get("max_calls", defaults.get("max_calls", 15)))
    target = int(cfg.get("target_series", defaults.get("target_series", 300)))

    summary = {"dataset": dataset, "catalog_size": 0, "calls": 0, "ok": 0, "failed": 0,
               "kb": 0.0, "seconds": 0.0, "rows": 0, "series": 0, "errors": [], "log": []}
    try:
        catalog = catalog_dataset(client, dataset, split_by)
    except BEAError as exc:
        summary["errors"].append(f"catalog: {exc}")
        log(f"  FAIL {dataset}: could not list {split_by}: {exc}")
        return summary
    summary["catalog_size"] = len(catalog)
    base = fill_required(client, dataset, cfg.get("params", {}), split_by)

    raw_dir = DATA / "raw" / dataset
    raw_dir.mkdir(parents=True, exist_ok=True)
    std_path = DATA / "standardized" / f"{dataset}.jsonl"
    std_path.parent.mkdir(parents=True, exist_ok=True)
    index = []

    with std_path.open("w") as std_out:
        for item in pick_evenly(catalog, max_calls):
            if summary["series"] >= target:
                break
            table = item["key"]
            try:
                attempts = _attempts(client, dataset, split_by, table, base)
            except Exception:
                attempts = [{**base, split_by: table}]
            row = {"dataset": dataset, "table": table, "status": "fail", "error": "", "kb": 0.0,
                   "seconds": 0.0, "rows": 0, "series": 0, "from_cache": False}
            for params in attempts:
                summary["calls"] += 1
                try:
                    results = client.get_data(dataset, use_cache=use_cache, **params)
                except (BEAError, Exception) as exc:  # network errors too: keep going
                    row["error"] = str(exc)[:200]
                    time.sleep(0 if client.last_from_cache else 1.0)  # stay well under 30 errors/min
                    continue
                records, stats = to_series(results, dataset, table, request=params)
                (raw_dir / f"{_safe_name(table)}.json").write_text(
                    json.dumps({"dataset": dataset, "request": params, "retrieved": date.today().isoformat(),
                                "results": results}))
                for rec in records:
                    std_out.write(json.dumps(rec) + "\n")
                    index.append(metadata_only(rec))
                row.update(status="ok", error="", kb=round(client.last_bytes / 1024, 1),
                           seconds=round(client.last_seconds, 2), rows=stats["rows"],
                           series=stats["series"], from_cache=client.last_from_cache)
                break
            summary["log"].append(row)
            if row["status"] == "ok":
                summary["ok"] += 1
                summary["kb"] += row["kb"]
                summary["seconds"] += row["seconds"]
                summary["rows"] += row["rows"]
                summary["series"] += row["series"]
                log(f"  ok   {dataset:<24} {table:<14} {row['series']:>5} series {row['kb']:>9.1f} KB")
            else:
                summary["failed"] += 1
                summary["errors"].append(f"{table}: {row['error']}")
                log(f"  FAIL {dataset:<24} {table:<14} {row['error'][:90]}")

    (DATA / "standardized" / f"{dataset}.index.json").write_text(json.dumps(index, indent=1))
    return summary


def _attempts(client, dataset, split_by, table, base) -> list[dict]:
    """Parameter sets to try for one table (more than one only for Regional fallbacks)."""
    params = {**base, split_by: table}
    if dataset != "Regional":
        return [params]
    line = "1"
    try:
        lines = _as_list(client.get_parameter_values_filtered(dataset, "LineCode", TableName=table))
        if lines and _key(lines[0]):
            line = _key(lines[0])
    except Exception:  # odd/empty answer: fall back to line 1, the GetData call will say if that's wrong
        pass
    return [{**params, "LineCode": line, "GeoFips": geo} for geo in regional_geo(table)]


# ---------- all datasets + report ----------

def run(config_path: str | Path = "config/datasets.yaml", only: list[str] | None = None,
        max_calls: int | None = None, target_series: int | None = None, use_cache: bool = True,
        client: BEAClient | None = None) -> list[dict]:
    cfg = yaml.safe_load(Path(config_path).read_text())
    defaults = dict(cfg.get("defaults", {}))
    if max_calls:
        defaults["max_calls"] = max_calls
    if target_series:
        defaults["target_series"] = target_series
    datasets = cfg["datasets"]
    if only:
        datasets = {k: v for k, v in datasets.items() if k in only}
    if max_calls:  # a CLI override beats per-dataset settings
        datasets = {k: {**v, "max_calls": min(int(v.get("max_calls", max_calls)), max_calls)}
                    for k, v in datasets.items()}

    client = client or BEAClient()
    summaries = []
    for name, dcfg in datasets.items():
        print(f"\n== {name}")
        summaries.append(download_dataset(client, name, dcfg, defaults, use_cache=use_cache))
    write_reports(summaries)
    return summaries


def write_reports(summaries: list[dict]) -> None:
    REPORTS.mkdir(exist_ok=True)
    with (REPORTS / "download_log.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        w.writeheader()
        for s in summaries:
            for row in s["log"]:
                w.writerow(row)

    lines = [
        "# BEA sample download: how heavy is each dataset?",
        "",
        f"Run on {date.today().isoformat()}. One GetData call per table; numbers are for the sample only.",
        "`Est. full size` = average KB per call x number of tables in the dataset (rough; Regional is",
        "much bigger in reality because every table also has many lines and geographies).",
        "",
        "| Dataset | Tables in catalog | Calls OK / tried | Series | Rows | Raw MB | Avg s/call | Est. full size (MB) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    tot = {"series": 0, "rows": 0, "kb": 0.0, "full": 0.0}
    for s in summaries:
        avg_kb = s["kb"] / s["ok"] if s["ok"] else 0
        full_mb = avg_kb * s["catalog_size"] / 1024
        avg_s = s["seconds"] / s["ok"] if s["ok"] else 0
        tried = s["ok"] + s["failed"]
        lines.append(f"| {s['dataset']} | {s['catalog_size']} | {s['ok']} / {tried} | {s['series']} | "
                     f"{s['rows']} | {s['kb'] / 1024:.2f} | {avg_s:.2f} | {full_mb:.0f} |")
        tot["series"] += s["series"]
        tot["rows"] += s["rows"]
        tot["kb"] += s["kb"]
        tot["full"] += full_mb
    lines.append(f"| **Total** | | | **{tot['series']}** | **{tot['rows']}** | **{tot['kb'] / 1024:.2f}** | | "
                 f"**{tot['full']:.0f}** |")
    errs = [(s["dataset"], e) for s in summaries for e in s["errors"]]
    if errs:
        lines += ["", "## Errors", ""] + [f"- **{d}** {e}" for d, e in errs[:60]]
    (REPORTS / "download_summary.md").write_text("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines[7:]))
    print(f"\nWrote reports/download_summary.md, reports/download_log.csv, data/standardized/*.jsonl")


def restandardize() -> dict:
    """Rebuild data/standardized/ from the raw files already on disk (no API calls).

    Handy when we change the JSON format: edit standardize_json.py, run this, done.
    """
    counts = {}
    out_dir = DATA / "standardized"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_root = DATA / "raw"
    if not raw_root.exists():
        raise SystemExit("No data/raw/ yet. Run `python -m bea_corpus download` first.")
    for ds_dir in sorted(p for p in raw_root.iterdir() if p.is_dir() and p.name != "cache"):
        index, n = [], 0
        with (out_dir / f"{ds_dir.name}.jsonl").open("w") as f:
            for raw in sorted(ds_dir.glob("*.json")):
                blob = json.loads(raw.read_text())
                req = blob.get("request", {})
                split_value = next((v for k, v in req.items() if k in SPLIT_PARAMS), raw.stem)
                records, _ = to_series(blob["results"], ds_dir.name, str(split_value), request=req)
                for rec in records:
                    f.write(json.dumps(rec) + "\n")
                    index.append(metadata_only(rec))
                n += len(records)
        (out_dir / f"{ds_dir.name}.index.json").write_text(json.dumps(index, indent=1))
        counts[ds_dir.name] = n
        print(f"  {ds_dir.name:<26} {n:>6} series")
    return counts


SPLIT_PARAMS = ("TableName", "TableID", "Indicator", "TypeOfInvestment", "TypeOfService", "Channel", "SeriesID")
