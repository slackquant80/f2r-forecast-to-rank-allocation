#!/usr/bin/env python3
"""Read-only F2R Streamlit live-version witness; never deploys or mutates hosting."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "src/dashboard/public_data/f2r_public_state.json"
MARKER = ROOT / "src/dashboard/static/release_identity.json"
SCHEMA = "F2R_PUBLIC_LIVE_IDENTITY_V1"
URL = "https://f2r-forecast-to-rank-allocation.streamlit.app/app/static/release_identity.json"
HEX = re.compile(r"^[0-9a-f]{64}$")


def expected_sha() -> str:
    raw = STATE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    marker = json.loads(MARKER.read_text(encoding="utf-8-sig"))
    if marker.get("schema") != SCHEMA or marker.get("public_state_sha256") != digest:
        raise ValueError("F2R_GITHUB_MAIN_SOURCE_MARKER_MISMATCH")
    return digest


def pull(expected: str, attempt: int) -> dict:
    req = Request(URL + "?sha=" + expected[:16] + "&probe=" + str(attempt),
                  headers={"Cache-Control": "no-cache", "Pragma": "no-cache",
                           "Accept": "application/json", "Accept-Encoding": "identity"})
    with urlopen(req, timeout=12) as resp:
        if resp.status != 200:
            raise ValueError("F2R_LIVE_WITNESS_HTTP_NOT_OK")
        payload = resp.read(8193)
    if len(payload) > 8192:
        raise ValueError("F2R_LIVE_WITNESS_OVERSIZED")
    value = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("F2R_LIVE_WITNESS_INVALID_DOCUMENT")
    return value


def check(expected: str, timeout: float, interval: float,
          getter=pull, clock=time.monotonic, sleeper=time.sleep) -> bool:
    if not HEX.fullmatch(expected) or timeout < 0 or interval <= 0:
        raise ValueError("F2R_LIVE_WITNESS_BAD_ARGS")
    deadline = clock() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            doc = getter(expected, attempt)
            if doc.get("schema") == SCHEMA and doc.get("public_state_sha256") == expected:
                print("F2R_LIVE_STREAMLIT_EXACT_PUBLIC_STATE_SHA256_PASS", expected)
                return True
            print("F2R_LIVE_PENDING_IDENTITY_STALE attempt", attempt)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError,
                UnicodeError, json.JSONDecodeError) as ex:
            print("F2R_LIVE_PENDING_HTTP_OR_RESPONSE attempt", attempt, type(ex).__name__)
        left = deadline - clock()
        if left <= 0:
            return False
        sleeper(min(interval, left))


def selftest() -> None:
    expected = "a" * 64
    now = [0.0]
    def clock(): return now[0]
    def sleep(v): now[0] += v
    count = [0]
    def fake(sha, attempt):
        count[0] += 1
        return {"schema": SCHEMA, "public_state_sha256":
                sha if attempt == 3 else "b" * 64}
    assert check(expected, 5, 1, fake, clock, sleep)
    assert count[0] == 3
    count[0] = 0
    assert not check(expected, 2, 1,
                     lambda sha, attempt: {"schema": SCHEMA, "public_state_sha256": "b" * 64},
                     clock, sleep)
    try:
        check("bad", 5, 1, fake, clock, sleep)
    except ValueError as e:
        assert "BAD_ARGS" in str(e)
    else:
        raise AssertionError("Invalid SHA accepted")
    print("F2R_LIVE_WITNESS_FAIL_CLOSED_SELFTEST_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--timeout-seconds", type=float, default=240)
    ap.add_argument("--interval-seconds", type=float, default=10)
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    expected = expected_sha()
    if check(expected, args.timeout_seconds, args.interval_seconds):
        return 0
    print("F2R_LIVE_STREAMLIT_UNVERIFIED_NOT_DEPLOYMENT_PROOF", expected, file=sys.stderr)
    return 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError) as e:
        print("F2R_LIVE_STREAMLIT_PRECHECK_HOLD", type(e).__name__, str(e), file=sys.stderr)
        raise SystemExit(2)
