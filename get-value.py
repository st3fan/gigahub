#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/


import json
import os
import sys

import gigahub


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: get-value.py <xpath>")

    if (github_access_token := os.getenv("GIGAHUB_PASSWORD")) is None:
        raise SystemExit("error: no GIGAHUB_PASSWORD set")

    session, reply = gigahub.open_session(username="admin", password=os.getenv("GIGAHUB_PASSWORD"))

    action = {
        "id": 0,
        "method": "getValue",
        "xpath": sys.argv[1],
        "options": {"nss": [{"name": "gtw", "uri": "http://sagemcom.com/gateway-data"}]},
    }

    session, reply = gigahub.send_session_request(session=session, actions=[action])

    print(json.dumps(reply, indent=2))

