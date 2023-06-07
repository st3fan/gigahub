#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

export GIGAHUB_PASSWORD=
export INFLUXDB_URL=
export INFLUXDB_TOKEN=
export INFLUXDB_BUCKET=
export INFLUXDB_ORG=

DIR=$(dirname "${BASH_SOURCE[0]}")
$DIR/.venv/bin/python $DIR/metrics.py

