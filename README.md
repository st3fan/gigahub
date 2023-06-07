# GigaHub
_Stefan Arentz, June 2023_

Random collection of things useful to interface with a GigaHub modem. Work in progress, works for me.

## Setup

```
$ git clone https://github.com/st3fan/gigahub.git
$ cd gigahub
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

## Metrics

The `metrics.py` script discovers all ethernet and optical interfaces and then sends the following metrics to an InfluxDB instance:

* `bytes_recv`
* `bytes_sent`
* `packets_recv`
* `packets_sent`

Simple dashboard that shows traffic on the optical interface:

![GigaHub Bytes Sent & Received](metrics.png?raw=true "GigaHub Bytes Sent & Received")


For my modem these are made available to InfluxDB as:

```json
{
  "measurement": "net",
  "tags": {
    "host": "gigahub",
    "interface": "eth0"
  },
  "fields": {
    "bytes_recv": 0,
    "bytes_sent": 0,
    "packets_recv": 0,
    "packets_sent": 0
  }
}
```

Where the `interface` maps to the LAN ports (`eth0` - `eth3`), the 10G port is `eth4` and for me the only optical port is `veip0`.

There is a lot more data available from the modem but my primary interest was network statistics. Feel free to file an Issue for a metric you want to see or submit a Pull Request.

Interaction with the modem's API is really fast and you can easily run it every minute from a cron job. The included `metrics.sh` script is good for that. Configure it with your settings and you can invoke it from `cron` or `systemd`.

```
#!/bin/bash

export GIGAHUB_PASSWORD=
export INFLUXDB_URL=
export INFLUXDB_TOKEN=
export INFLUXDB_BUCKET=
export INFLUXDB_ORG=

DIR=$(dirname "${BASH_SOURCE[0]}")
$DIR/.venv/bin/python $DIR/metrics.py
```

The `GIGAHUB_PASSWORD` is the administrative password that you also use to log in to the modem's dashboard. Just make sure you have the `.venv` setup. It is easy to test the script - just invoke it and it should be silent if all is good.

I have only tested it with my own InfluxDB 2.7 server but it probably works fine with their hosted service too.

> Feel free to leave a bug report or open a feature request at [https://github.com/st3fan/gigahub/issues](github.com/st3fan/gigahub/issues).

