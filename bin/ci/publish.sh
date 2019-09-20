#!/usr/bin/env bash

set -euxo pipefail

cd /srv
echo "[pypi]" >> ~/.pypirc
echo "username=$PYPI_USERNAME" >> ~/.pypirc
echo "password=$PYPI_PASSWORD" >> ~/.pypirc

twine upload --repository pypi dist/*
