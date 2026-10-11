#!/usr/bin/env python3
"""Validate a public F2R release artifact before a reviewed PR can be merged.

The current legacy main may not have a live identity witness; this auditor
never equates a legacy deploy with a verified release. No data recomputation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

RELEASE_FILES = frozenset({
    ".gitattributes", ".gitignore", ".streamlit/config.toml",
    "README.md", "requirements.txt", "src/dashboard/app.py",
    "src/dashboard/portfolio_history_export.py",
    "src/dashboard/public_app.py",
    "src/dashboard/public_data/f2r_public_state.json",
    "src/dashboard/reader_presentation.json",
    "src/dashboard/static/release_identity.json",
})
MANIFEST = "release_manifest.json"
STATE = "src/dashboard/public_data/f2r_public_state.json"
WITNESS = "src/dashboard/static/release_identity.json"
SOURCE_PATHS = frozenset({"src/dashboard/app.py","src/dashboard/public_app.py",
                          "src/dashboard/portfolio_history_export.py"})


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(root):
    root = root.resolve(strict=True)
    raw = {}
    for name in RELEASE_FILES | {MANIFEST}:
        file = root / name
        require(file.is_file() and not file.is_symlink(), "F2R_RELEASE_FILE_MISSING: " + name)
        require(all(not p.is_symlink() for p in file.parents if p != root and root in p.parents),
                "F2R_PARENT_SYMLINK_HOLD: " + name)
        raw[name] = file.read_bytes()
        require(0 < len(raw[name]) <= 30000000, "F2R_FILE_SIZE_HOLD: " + name)
    manifest = json.loads(raw[MANIFEST].decode("utf-8-sig"))
    require(manifest.get("schema_version") == "1.0" and
            manifest.get("system") == "Forecast-to-Rank Allocation",
            "F2R_MANIFEST_SCHEMA_HOLD")
    checks = manifest.get("files")
    require(isinstance(checks, dict) and set(checks) == RELEASE_FILES,
            "F2R_MANIFEST_FILES_HOLD")
    for name in RELEASE_FILES:
        require(checks[name] == sha(raw[name]), "F2R_MANIFEST_SHA_HOLD: " + name)
    # Extra files in the deployment boundary are forbidden; CI infrastructure
    # is outside this set and intentionally not transported from source.
    actual = {p.relative_to(root).as_posix() for p in (root / "src/dashboard").rglob("*") if p.is_file()}
    expected = {p for p in RELEASE_FILES if p.startswith("src/dashboard/")}
    require(actual == expected, "F2R_DASHBOARD_EXTRA_OR_MISSING_FILE_HOLD")
    witness = json.loads(raw[WITNESS].decode("utf-8-sig"))
    require(witness.get("schema") == "F2R_PUBLIC_LIVE_IDENTITY_V1" and
            witness.get("public_state_sha256") == sha(raw[STATE]),
            "F2R_LIVE_STATE_WITNESS_HOLD")
    state = json.loads(raw[STATE].decode("utf-8-sig"))
    require(state.get("schema_version") == "2.0", "F2R_PUBLIC_SCHEMA_HOLD")
    live = state.get("live_state", {})
    official = live.get("official", {})
    preview = live.get("preview", {})
    current = live.get("current_mtd", {})
    perf = state.get("completed_performance", {})
    comp = state.get("benchmark_comparison", {})
    holdings = official.get("holdings", [])
    require(isinstance(holdings, list) and len(holdings) == 4 and
            len({x.get("asset") for x in holdings}) == 4 and
            abs(sum(float(x["target_weight"]) for x in holdings) - 1) < 1e-10,
            "F2R_OFFICIAL_TARGET_ACCOUNTING_HOLD")
    require(perf.get("identity") == "CURRENT_CANONICAL_MODEL_PORTFOLIO" and
            perf.get("version_splice") is False and
            perf.get("growth_frequency") == perf.get("drawdown_frequency") == "DAILY",
            "F2R_COMPLETED_PERFORMANCE_IDENTITY_HOLD")
    require(str(perf.get("completed_through_month", "")) <
            str(official.get("holding_month", "")) and
            str(current.get("holding_month", "")) == str(official.get("holding_month", "")),
            "F2R_COMPLETED_CURRENT_CLOCK_HOLD")
    require(str(perf.get("support_end", ""))[:7] ==
            str(perf.get("completed_through_month", "")),
            "F2R_PERFORMANCE_SUPPORT_CLOCK_HOLD")
    require(bool(perf.get("growth_series")) and
            perf["growth_series"][-1].get("date") == perf.get("support_end"),
            "F2R_DAILY_SERIES_SUPPORT_HOLD")
    require(current.get("authority") == "MODEL_PORTFOLIO_MARK" and
            (not current.get("available") or
             (current.get("mtd_return") is not None and current.get("as_of_date"))),
            "F2R_CURRENT_ACCOUNTING_HOLD")
    if preview.get("available"):
        require(len(preview.get("holdings", [])) == 4 and
                str(preview.get("prospective_holding_month", "")) >
                str(official.get("holding_month", "")),
                "F2R_PREVIEW_PROSPECTIVE_HOLD")
    require(comp.get("frequency") == "DAILY" and
            comp.get("support_end") == perf.get("support_end") and
            comp.get("support_start") == perf.get("support_start") and
            len(comp.get("summary", [])) == 3,
            "F2R_BENCHMARK_SAME_CLOCK_HOLD")
    for name in SOURCE_PATHS:
        compile(raw[name], name, "exec")
    # Small, explicit leak-deny for files traveling to a PUBLIC repo.
    for name in RELEASE_FILES:
        if Path(name).suffix not in {".py", ".json", ".md", ".toml", ".txt"}:
            continue
        contents = raw[name].decode("utf-8-sig")
        for token in ("_LOCAL_PRIVATE_DATA", "## Research", "C:\\SK_Main", "C:\\Users\\",
                      "sk_test_", "ghp_", "github_pat_"):
            require(token.lower() not in contents.lower(), "F2R_PRIVATE_TOKEN_HOLD: " + name)
    return {"status":"F2R_RELEASE_STRICT_VERIFIED","official":official["signal_period"],
            "holding_month":official["holding_month"],"state_sha256":sha(raw[STATE]),
            "file_count":len(RELEASE_FILES)}


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name in RELEASE_FILES:
            p = root/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"sample\n")
        # The negative tests must fail CLOSED even before financial checks.
        try:
            audit(root)
        except ValueError as exc:
            assert "F2R_RELEASE_FILE_MISSING: release_manifest.json" in str(exc), str(exc)
        else:
            raise AssertionError("Missing manifest was accepted")
        (root / WITNESS).write_text(json.dumps({
            "schema":"F2R_PUBLIC_LIVE_IDENTITY_V1",
            "public_state_sha256":"0" * 64}))
        (root / MANIFEST).write_text(json.dumps({
            "schema_version":"1.0","system":"Forecast-to-Rank Allocation",
            "files":{name:sha((root/name).read_bytes()) for name in RELEASE_FILES}}))
        try:
            audit(root)
        except ValueError as exc:
            assert "F2R_LIVE_STATE_WITNESS_HOLD" in str(exc), str(exc)
        else:
            raise AssertionError("Fabricated witness was accepted")
        (root/"src/dashboard/app.py").write_bytes(b"tampered")
        try:
            audit(root)
        except ValueError as exc:
            assert "F2R_MANIFEST_SHA_HOLD" in str(exc)
        else:
            raise AssertionError("Changed release code was accepted")
    print("F2R_PUBLIC_PR_STRICT_RELEASE_NEGATIVE_TEST_PASS")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--validate-release", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        print(json.dumps(audit(args.validate_release),sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, SyntaxError, UnicodeError, OSError,
            json.JSONDecodeError) as exc:
        print("F2R_PUBLIC_REVIEW_CI_HOLD", type(exc).__name__, str(exc), file=sys.stderr)
        raise SystemExit(2)
