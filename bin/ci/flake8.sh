#!/usr/bin/env bash

set -euxo pipefail

cd /srv
mkdir -p workspace/test-results
flake8 . | tee ./workspace/test-results/flake8.txt
