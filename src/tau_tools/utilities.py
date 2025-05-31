import os
import time
from typing import Any, Dict, Optional

import requests


def request(
    method: str,
    url: str,
    s: Optional[requests.Session] = None,
    delay=1,
    json: Optional[Any] = None,
    data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    cache_category: Optional[str] = None,
    cache_key: Optional[str] = None,
) -> str:
    if cache_category is None:
        cache_file = f"cache/{cache_key}.txt"
    else:
        cache_file = f"cache-{cache_category}/{cache_key}.txt"

    if (
        cache_key is not None
        and os.path.exists(cache_file)
        and not (
            "TAU_TOOLS_FORCE_FETCH" in os.environ
            and len(os.environ["TAU_TOOLS_FORCE_FETCH"]) != 0
        )
    ):
        with open(cache_file, "r") as f:
            response_text = f.read()
        return response_text

    response = (
        s.request(method, url, json=json, data=data, headers=headers)
        if s is not None
        else requests.request(method, url, json=json, data=data, headers=headers)
    )
    time.sleep(delay)

    if cache_key is not None:
        cache_directory = os.path.dirname(os.path.abspath(cache_file))
        if not os.path.isdir(cache_directory):
            os.mkdir(cache_directory)
        with open(cache_file, "w") as f:
            f.write(response.text)

    return response.text


def try_float(s: str):
    try:
        return float(s)
    except ValueError:
        return s


def try_int(s: str):
    try:
        return int(s)
    except ValueError:
        return s
