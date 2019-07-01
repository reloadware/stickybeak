#!/srv/.venv/bin/python

import requests
import time

timeout = 25

while True:
    try:
        response = requests.get('http://django-srv:8000/health-check/')
        if response.status_code == 200:
            break
    except requests.exceptions.ConnectionError:
        pass

    time.sleep(1)
    timeout -= 1

    if timeout == 0:
        print("timeout")
        exit(1)
