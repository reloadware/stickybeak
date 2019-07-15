#!/srv/.venv/bin/python

import os
import time

import requests

timeout: int = 40

while True:
    try:
        django_srv_hostname: str = os.getenv("DJANGO_SRV_HOSTNAME")
        response: requests.Response = requests.get(f'http://{django_srv_hostname}/health-check/')
        if response.status_code == 200:
            break
    except requests.exceptions.ConnectionError:
        pass

    time.sleep(1)
    timeout -= 1

    if timeout == 0:
        print("timeout")
        exit(1)
