from __future__ import annotations

import time
from typing import Any

import requests


DEFAULT_HEADERS = {
    "User-Agent": "thesis-reading-skill/0.1 (+https://github.com/)"
}


class SourceError(RuntimeError):
    pass


def get_json(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: int = 30) -> dict[str, Any]:
    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)

    delays = [0, 2, 5, 10]
    last_error: Exception | None = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        try:
            response = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    time.sleep(min(int(retry_after), 30))
                    continue
                raise SourceError(f"Rate limited by source: {url}")
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError, SourceError) as exc:
            last_error = exc
            continue
    raise SourceError(f"Failed to fetch JSON from {url}: {last_error}")
