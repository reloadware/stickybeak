#!/usr/bin/env bash

set -euxo pipefail

cd /srv
mkdir -p workspace/test-results
cd tests
pytest --cov-config=.coveragerc --cov=stickybeak --junitxml=/srv/workspace/test-results/summary.xml --cov-report=xml
