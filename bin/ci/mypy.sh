#!/usr/bin/env bash

set -euxo pipefail

cd /srv
mkdir -p workspace/test-results
mypy . | tee ./workspace/test-results/mypy.txt
