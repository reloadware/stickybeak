from dataclasses import dataclass
import json
from math import ceil
from pathlib import Path
import re
from typing import Any, Dict
from urllib.parse import urljoin

from requests import Session
from requests.adapters import HTTPAdapter, Response
from urllib3 import Retry


class SubSecondRetry(Retry):
    """Handle floats like: Retry-After: 0.223"""

    def parse_retry_after(self, retry_after: str) -> float:
        if re.match(r"^\s*[0-9]+\.*[0-9]+\s*$", retry_after):
            return ceil(float(retry_after))
        return super().parse_retry_after(retry_after)


@dataclass
class Client:
    base_url: str

    def __post_init__(self) -> None:
        self._retry_session = Session()

        retry = SubSecondRetry(total=6, read=6, connect=6, status=6, backoff_factor=0.1)
        self._retry_session.mount("http://", HTTPAdapter(max_retries=retry))
        self._retry_session.mount("https://", HTTPAdapter(max_retries=retry))

        self._session = Session()
        self._session.mount("http://", HTTPAdapter())
        self._session.mount("https://", HTTPAdapter())

    def get(self, url: str) -> Dict[str, Any]:
        joined_url = urljoin(self.base_url, url)
        response: Response = self._retry_session.get(joined_url)
        response.raise_for_status()
        return json.loads(response.content or "null")

    def post(self, url: str, data: bytes) -> Response:
        joined_url = urljoin(self.base_url, url)

        response: Response = self._session.post(joined_url, data=data, timeout=60)
        response.raise_for_status()
        return response


def get_site_packages_dir_from_venv(venv: Path) -> Path:
    ret = next((venv / "lib").glob("*"))
    if ret.name != "site-packages":
        ret /= "site-packages"
    return ret
