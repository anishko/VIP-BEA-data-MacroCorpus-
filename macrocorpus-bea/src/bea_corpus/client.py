"""Thin, polite client for the BEA Data API (https://apps.bea.gov/api/data).

- One endpoint, five methods (GetDataSetList, GetParameterList,
  GetParameterValues, GetParameterValuesFiltered, GetData).
- Stays under BEA's limits (100 requests/min, 100 MB/min, 30 errors/min)
  by spacing requests and backing off on HTTP 429 using Retry-After.
- Caches raw JSON responses on disk so re-runs don't re-download.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://apps.bea.gov/api/data"


class BEAError(RuntimeError):
    """Raised when the API returns an error object instead of data."""


class BEAClient:
    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: str | Path | None = "data/raw/cache",
        min_interval: float = 0.75,  # ~80 requests/min, under the 100/min limit
        max_retries: int = 3,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("BEA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No BEA API key. Set BEA_API_KEY in your environment or .env "
                "(register at https://apps.bea.gov/API/signup/)."
            )
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.timeout = timeout
        self._last_request = 0.0
        self._session = requests.Session()

    # ---------- public methods ----------

    def get_dataset_list(self) -> list[dict]:
        return self._results("GetDataSetList")["Dataset"]

    def get_parameter_list(self, dataset: str) -> list[dict]:
        return self._results("GetParameterList", DatasetName=dataset)["Parameter"]

    def get_parameter_values(self, dataset: str, parameter: str) -> list[dict]:
        res = self._results("GetParameterValues", DatasetName=dataset, ParameterName=parameter)
        return res.get("ParamValue", [])

    def get_parameter_values_filtered(self, dataset: str, target: str, **filters: Any) -> list[dict]:
        res = self._results(
            "GetParameterValuesFiltered", DatasetName=dataset, TargetParameter=target, **filters
        )
        return res.get("ParamValue", [])

    def get_data(self, dataset: str, use_cache: bool = True, **params: Any) -> dict:
        """Return the raw `Results` object for a GetData call."""
        return self._results("GetData", use_cache=use_cache, DatasetName=dataset, **params)

    # ---------- internals ----------

    def _results(self, method: str, use_cache: bool = True, **params: Any) -> dict:
        query = {"method": method, "ResultFormat": "JSON", **{k: _fmt(v) for k, v in params.items()}}
        cache_file = self._cache_path(query)
        if use_cache and cache_file and cache_file.exists():
            payload = json.loads(cache_file.read_text())
        else:
            payload = self._request(query)
            # BEA echoes the request, including your UserID, back in the
            # response. Drop it so the key never lands in cache files.
            if isinstance(payload.get("BEAAPI"), dict):
                payload["BEAAPI"].pop("Request", None)
            if cache_file:
                cache_file.write_text(json.dumps(payload))
        return extract_results(payload)

    def _request(self, query: dict) -> dict:
        params = {"UserID": self.api_key, **query}
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()
            resp = self._session.get(BASE_URL, params=params, timeout=self.timeout)
            if resp.status_code == 429 and attempt < self.max_retries:
                time.sleep(float(resp.headers.get("Retry-After", 60)) + 1)
                continue
            resp.raise_for_status()
            return resp.json()
        raise BEAError("Gave up after repeated throttling (HTTP 429).")

    def _cache_path(self, query: dict) -> Path | None:
        if not self.cache_dir:
            return None
        key = json.dumps(query, sort_keys=True)  # API key deliberately excluded
        return self.cache_dir / f"{hashlib.sha1(key.encode()).hexdigest()[:16]}.json"


def extract_results(payload: dict) -> dict:
    """Unwrap BEAAPI -> Results, normalising the shapes different datasets use."""
    try:
        results = payload["BEAAPI"]["Results"]
    except (KeyError, TypeError) as exc:
        raise BEAError(f"Unexpected response shape: {str(payload)[:300]}") from exc
    # Some datasets (e.g. ITA) wrap Results in a one-element list.
    if isinstance(results, list):
        results = results[0] if results else {}
    error = results.get("Error") or payload["BEAAPI"].get("Error")
    if error:
        desc = error.get("APIErrorDescription", error)
        detail = error.get("ErrorDetail", {})
        raise BEAError(f"{desc} {detail.get('Description', '') if isinstance(detail, dict) else detail}".strip())
    return results


def _fmt(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)
