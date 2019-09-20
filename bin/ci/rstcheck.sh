#!/usr/bin/env bash

set -euxo pipefail

cd /srv
mkdir -p workspace/test-results
rstcheck README.rst | tee ./workspace/test-results/rstcheck.txt
