#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

import json
import os
import sys
import time

import gigahub

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


def discover_interfaces(session: dict, type: str) -> tuple[dict, dict]:
    action = {
        "id": 0,
        "method": "getValue",
        "xpath": f"Device/{type}/Interfaces",
        "options": {"nss": [{"name": "gtw", "uri": "http://sagemcom.com/gateway-data"}]},
    }

    session, reply = gigahub.send_session_request(session=session, actions=[action])
    if reply["error"]["code"] != gigahub.XMO_REQUEST_NO_ERR:
        raise Exception(f'Unexpected error <{reply["error"]["code"]}>: <{reply["error"]["description"]}>')

    interfaces = {}
    for interface in reply["actions"][0]["callbacks"][0]["parameters"]["value"]:
        if interface["IfcName"]:
            interfaces[interface["IfcName"]] = f"Device/{type}/Interfaces/Interface[@uid='{interface['uid']}']/Stats"

    return session, interfaces


if __name__ == "__main__":
    session, reply = gigahub.open_session(username="admin", password=os.getenv("GIGAHUB_PASSWORD"))
    if reply["error"]["code"] != gigahub.XMO_REQUEST_NO_ERR:
        raise Exception(f'Unexpected error <{reply["error"]["code"]}>: <{reply["error"]["description"]}>')

    # Discover Interfaces

    session, ethernet_interfaces = discover_interfaces(session, "Ethernet")
    session, fiber_interfaces = discover_interfaces(session, "Optical")

    interfaces = ethernet_interfaces | fiber_interfaces

    # Collect metrics

    actions = []

    for if_index, (if_name, if_xpath) in enumerate(interfaces.items()):
        actions.append({
            "id": if_index,
            "method": "getValue",
            "xpath": if_xpath,
            "options": {"nss": [{"name": "gtw", "uri": "http://sagemcom.com/gateway-data"}]},
        })

    session, reply = gigahub.send_session_request(session=session, actions=actions)
    if reply["error"]["code"] != gigahub.XMO_REQUEST_NO_ERR:
        raise Exception(f'Unexpected error <{reply["error"]["code"]}>: <{reply["error"]["description"]}>')

    client = InfluxDBClient(url=os.getenv("INFLUXDB_URL"), token=os.getenv("INFLUXDB_TOKEN"), org=os.getenv("INFLUXDB_ORG"))
    write_api = client.write_api(write_options=SYNCHRONOUS)

    now = int(time.time() * 1000000000)

    for if_index, (if_name, if_xpath) in enumerate(interfaces.items()):
        metrics = reply["actions"][if_index]["callbacks"][0]["parameters"]["value"]["Stats"]

        point = Point("net").tag("host", "gigahub").tag("interface", if_name)
        point = point.field("packets_recv", int(metrics["PacketsReceived"])).field("packets_sent", int(metrics["PacketsSent"]))
        point = point.field("bytes_recv", int(metrics["BytesReceived"])).field("bytes_sent", int(metrics["BytesSent"]))
        point = point.time(now)

        write_api.write(bucket=os.getenv("INFLUXDB_BUCKET"), record=point)

