import time
from pathlib import Path

import requests

from private.auth import IS_SIMULATION, REAL, SIM

CONF = SIM if IS_SIMULATION else REAL
URL_BASE = CONF["URL_BASE"]
APP_KEY = CONF["APP_KEY"]
APP_SECRET = CONF["APP_SECRET"]
CANO = CONF["CANO"]
ACNT_PRDT_CD = CONF["ACNT_PRDT_CD"]
TR_PREFIX = "V" if IS_SIMULATION else "T"

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ("token_sim.dat" if IS_SIMULATION else "token_real.dat")
TOKEN_TTL = 23 * 3600
TIMEOUT = 10


def _issue_token():
    res = requests.post(
        f"{URL_BASE}/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET},
        timeout=TIMEOUT,
    )
    res.raise_for_status()
    token = res.json()["access_token"]
    TOKEN_FILE.write_text(f"{token}|{int(time.time())}")
    return token


def get_token(refresh=False):
    if not refresh and TOKEN_FILE.exists():
        try:
            token, issued = TOKEN_FILE.read_text().split("|")
            if time.time() - int(issued) < TOKEN_TTL:
                return token
        except ValueError:
            pass
    return _issue_token()


def request(method, path, tr_id, params=None, body=None):
    refresh = False
    for _ in range(3):
        try:
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {get_token(refresh)}",
                "appkey": APP_KEY,
                "appsecret": APP_SECRET,
                "tr_id": tr_id,
                "custtype": "P",
            }
            res = requests.request(
                method, URL_BASE + path, headers=headers, params=params, json=body, timeout=TIMEOUT
            )
            data = res.json()
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"[API_ERROR] {path} {e}")
            return None

        code = data.get("msg_cd")
        if res.status_code == 401 or code == "EGW00123":
            refresh = True
            continue
        if code == "EGW00201":
            time.sleep(1)
            continue
        if data.get("rt_cd") == "0":
            return data
        print(f"[API_ERROR] {path} {code} {data.get('msg1') or res.status_code}")
        return None

    print(f"[API_ERROR] {path} 재시도 초과")
    return None
