from dataclasses import dataclass
import json
from math import ceil
from pathlib import Path
import re
import sys
from time import sleep
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from requests import HTTPError, Session
from requests.adapters import HTTPAdapter, Response
from urllib3 import Retry


class FastRetry(Retry):
    def sleep(self, response: Any = None) -> None:
        sleep(0.1)


@dataclass
class Client:
    base_url: str

    def __post_init__(self) -> None:
        self._retry_session = Session()

        retry = FastRetry(total=20)
        self._retry_session.mount("http://", HTTPAdapter(max_retries=retry))
        self._retry_session.mount("https://", HTTPAdapter(max_retries=retry))

        self._session = Session()
        self._session.mount("http://", HTTPAdapter())
        self._session.mount("https://", HTTPAdapter())

    def get(self, url: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        joined_url = urljoin(self.base_url, url)
        if timeout:
            session = Session()
            tries = int(timeout // 0.1)

            retry = FastRetry(total=tries)
            session.mount("http://", HTTPAdapter(max_retries=retry))
            session.mount("https://", HTTPAdapter(max_retries=retry))
            response = session.get(joined_url)
        else:
            response = self._retry_session.get(joined_url)

        try:
            response.raise_for_status()
        except HTTPError:
            sys.stderr.write(response.text)
            sys.stderr.flush()
            raise

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
