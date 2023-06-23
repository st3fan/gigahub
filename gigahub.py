#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

import hashlib
import json
import os
import random
import urllib.parse

import requests

GIGAHUB_URL = os.getenv("GIGAHUB_URL") or "http://192.168.2.1";

GUI_PASSWORD_SALT = ""

XMO_REQUEST_NO_ERR = 16777216

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": GIGAHUB_URL,
    "Referer": GIGAHUB_URL,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}


def make_guest_cookies(*, request_id: int, session_id: int, device_nonce: str) -> dict:
    ha1 = hash_sha512("guest" + ":" + device_nonce + ":" + hash_encoder_pass("guest", ""))  # username:device_nonce:password
    cookies = {
        "bell_session": urllib.parse.quote_plus(
            json.dumps(
                {
                    "req_id": request_id + 1,  # zero based for the request, 1 based here
                    "sess_id": "0" if session_id == 0 else session_id,
                    "basic": False,
                    "user": "guest",
                    "dataModel": {"name": "Internal", "nss": [{"name": "gtw", "uri": "http://sagemcom.com/gateway-data"}]},
                    "ha1": ha1[:10] + hash_encoder_pass("guest", "") + ha1[10:],
                    "nonce": device_nonce,
                },
                separators=(",", ":"),
            )
        )
    }
    return cookies


def make_request(*, id: int, session_id: int, priority: bool, actions: list[dict]):
    return {
        "request": {
            "id": id,
            "session-id": "0" if session_id == 0 else session_id,
            "priority": priority,
            "actions": actions,
        }
    }


def make_login_action(*, id: int, username: str):
    return {
        "id": id,
        "method": "logIn",
        "parameters": {
            "user": username,
            "persistent": "true",
            "session-options": {
                "nss": [{"name": "gtw", "uri": "http://sagemcom.com/gateway-data"}],
                "context-flags": {"get-content-name": True, "local-time": True, "no-default": False},
                "capability-depth": 2,
                "capability-flags": {"name": True, "default-value": False, "restriction": True, "description": False},
                "time-format": "ISO_8601",
                "compatibility-flags": {"flags": True, "default-value": True, "type": True},
                "depth": 2,
                "write-only-string": "_XMO_WRITE_ONLY_",
                "undefined-write-only-string": "_XMO_UNDEFINED_WRITE_ONLY_",
            },
        },
    }


def hash_sha512(s: str) -> str:
    return hashlib.sha512(s.encode()).hexdigest()


def hash_encoder_pass(username: str, password: str) -> str:
    if GUI_PASSWORD_SALT:
        return hash_sha512(password + ":" + GUI_PASSWORD_SALT)
    return hash_sha512(password)


def sign_request(
    *,
    request: dict,
    request_index: int,
    username: str,
    password: str | None,
    device_nonce: str = "",
    client_nonce: int | None = None,
) -> dict:
    if client_nonce is None:
        client_nonce = random.randint(0x100000, 0xFFFFFFFF)
    h = hash_sha512(username + ":" + device_nonce + ":" + hash_encoder_pass(username, password))
    auth_key = hash_sha512(h + ":" + str(request_index) + ":" + str(client_nonce) + ":" + "JSON:/cgi/json-req")

    request["request"]["cnonce"] = client_nonce
    request["request"]["auth-key"] = auth_key

    return request


def open_session(*, endpoint: str = GIGAHUB_URL+"/cgi/json-req", username: str, password: str) -> tuple[dict, dict]:
    login_request = make_request(id=0, session_id=0, priority=True, actions=[make_login_action(id=0, username=username)])
    login_request = sign_request(request=login_request, request_index=0, username=username, password=password)

    # Looks like the cookies are only there to save/restore state and are not checked on the server side.

    # cookies = make_guest_cookies(
    #     request_id=0,
    #     session_id=0,
    #     device_nonce="",
    # )

    r = requests.post(endpoint, data={"req": json.dumps(login_request)}, headers=HEADERS)  # , cookies=cookies)
    r.raise_for_status()

    reply = r.json()["reply"]
    if reply["error"]["code"] != XMO_REQUEST_NO_ERR:
        raise Exception(f'Unexpected error <{reply["error"]["code"]}>: <{reply["error"]["description"]}>')

    session = {
        "endpoint": endpoint,
        "id": reply["actions"][0]["callbacks"][0]["parameters"]["id"],
        "nonce": reply["actions"][0]["callbacks"][0]["parameters"]["nonce"],
        "request_count": 1,
        "username": username,
        "password": password,
    }

    return session, reply


def open_guest_session(*, endpoint: str = GIGAHUB_URL+"/cgi/json-req"):
    return open_session(endpoint=endpoint, username="guest", password="")


def send_session_request(*, session: dict, actions: list[dict]) -> tuple[dict, dict]:
    request = make_request(id=session["request_count"], session_id=session["id"], priority=False, actions=actions)
    request = sign_request(
        request=request,
        request_index=session["request_count"],
        username=session["username"],
        password=session["password"],
        device_nonce=session["nonce"],
    )

    # Looks like the cookies are only there to save/restore state and are not checked on the server side.

    # cookies = make_guest_cookies(
    #     request_id=session["request_count"],
    #     session_id=session["id"],
    #     device_nonce=session["nonce"],
    # )

    r = requests.post(session["endpoint"], data={"req": json.dumps(request)}, headers=HEADERS)  # , cookies=cookies)
    r.raise_for_status()

    session["request_count"] += 1

    reply = r.json()["reply"]

    # if reply["error"]["code"] != XMO_REQUEST_NO_ERR:
    #     raise Exception(f'Unexpected error <{reply["error"]["code"]}>: <{reply["error"]["description"]}>')

    return session, reply

