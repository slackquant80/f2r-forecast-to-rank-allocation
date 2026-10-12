#!/usr/bin/env python3
"""Receive a private, pinned F2R review-only ZIP into a DRAFT PR workspace.

Default: strict read-only preflight. --stage-reviewed may write only the
versioned public release allowlist. NEVER deploys, commits or merges.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from verify_release import RELEASE_FILES, MANIFEST, STATE, audit

ALLOWED = RELEASE_FILES | {MANIFEST}
MAX_SINGLE = 30_000_000
MAX_TOTAL = 50_000_000


def require(flag, why):
    if not flag:
        raise ValueError(why)


def inspect_zip(z):
    require(z.is_file(), "F2R_REVIEW_BUNDLE_MISSING")
    with zipfile.ZipFile(z) as f:
        infos = f.infolist()
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)), "F2R_DUPLICATE_ZIP_MEMBER_HOLD")
        require(set(names) == ALLOWED, "F2R_ZIP_EXACT_RELEASE_FILE_SCOPE_HOLD")
        require(sum(i.file_size for i in infos) <= MAX_TOTAL, "F2R_ZIP_TOTAL_SIZE_HOLD")
        for i in infos:
            require(i.filename in ALLOWED and
                    not i.filename.startswith("/") and
                    "\\" not in i.filename and ".." not in i.filename.split("/"),
                    "F2R_INVALID_MEMBER_PATH_HOLD")
            require(i.file_size > 0 and i.file_size <= MAX_SINGLE,
                    "F2R_ZIP_MEMBER_SIZE_HOLD")
            # S_IFLNK = 0o120000; a Unix symlink cannot escape the temp root.
            require((i.external_attr >> 16) & 0o170000 != 0o120000,
                    "F2R_ZIP_SYMLINK_HOLD")
        return {name: f.read(name) for name in names}


def clock(state):
    live = state["live_state"]
    return (
        str(live["official"]["signal_period"]),
        str(live["official"]["holding_month"]),
        str(state["completed_performance"]["support_end"]),
    )


def assess(bundle, root, *, stage=False):
    root = root.resolve(strict=True)
    source = inspect_zip(bundle)
    with tempfile.TemporaryDirectory(prefix="f2r-public-review-") as t:
        frozen = Path(t)
        for name, raw in source.items():
            path = frozen/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        candidate = audit(frozen)
    # Financial nonregression: no silent clock rollback of current Official
    # or completed history. Never compare against an unverified public witness.
    prior_path = root / STATE
    if prior_path.is_file():
        prior_clock = clock(json.loads(prior_path.read_text(encoding="utf-8-sig")))
        new_clock = clock(json.loads(source[STATE].decode("utf-8-sig")))
        require(new_clock[0] >= prior_clock[0] and
                new_clock[1] >= prior_clock[1] and
                new_clock[2] >= prior_clock[2],
                "F2R_PUBLIC_CLOCK_REGRESSION_HOLD")
    material = sorted(name for name in RELEASE_FILES
                      if not (root/name).is_file() or (root/name).read_bytes() != source[name])
    changed = sorted(name for name in ALLOWED
                     if not (root/name).is_file() or (root/name).read_bytes() != source[name])
    if not stage:
        print(json.dumps({"status":"F2R_SOURCE_RELEASE_REVIEWED_NO_WRITE",
                          "changed_files":changed,"material_files":material,
                          "public_state_sha256":candidate["state_sha256"]},sort_keys=True))
        return len(material) > 0
    require(material, "F2R_NO_MATERIAL_CHANGE_NO_PR_REQUIRED")
    # Explicitly never touches CI/workflow, other systems, or .git.
    for name in changed:
        target = root/name
        require(not target.is_symlink() and
                all(not p.is_symlink() for p in target.parents if p != root and root in p.parents),
                "F2R_UNTRUSTED_TARGET_HOLD")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source[name])
    audit(root)
    print("F2R_REVIEW_RELEASE_STAGE_ONLY_VERIFIED")
    return True


def selftest():
    with tempfile.TemporaryDirectory() as temp:
        d = Path(temp)
        zipfile_path = d/"candidate.zip"
        with zipfile.ZipFile(zipfile_path,"w") as z:
            z.writestr("../unexpected", "fake")
        try:
            inspect_zip(zipfile_path)
        except ValueError as ex:
            assert "EXACT_RELEASE_FILE_SCOPE_HOLD" in str(ex)
        else:
            raise AssertionError("Traversal accepted")
        with zipfile.ZipFile(zipfile_path,"w") as z:
            z.writestr(MANIFEST, "{}")
            z.writestr(MANIFEST, "{}")
        try:
            inspect_zip(zipfile_path)
        except ValueError as ex:
            assert "DUPLICATE_ZIP_MEMBER_HOLD" in str(ex)
        else:
            raise AssertionError("Duplicate accepted")
    print("F2R_PRIVATE_REVIEW_RECEIVER_NO_WRITE_NEGATIVE_TEST_PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle",type=Path)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--stage-reviewed",action="store_true")
    ap.add_argument("--selftest",action="store_true")
    args=ap.parse_args()
    if args.selftest:
        selftest()
        return 0
    require(args.bundle is not None,"F2R_PRIVATE_REVIEW_ZIP_REQUIRED")
    assess(args.bundle,args.root,stage=args.stage_reviewed)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile,
            json.JSONDecodeError, SyntaxError) as ex:
        print("F2R_PRIVATE_REVIEW_RECEIVER_HOLD",type(ex).__name__,str(ex),file=sys.stderr)
        raise SystemExit(2)
