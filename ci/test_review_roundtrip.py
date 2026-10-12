#!/usr/bin/env python3
"""Prove private review ZIP receiver accepts a real PUBLIC F2R snapshot safely.

Uses only files already committed to this public repository. No local model
execution, secret access, source repository calls or deployment.
"""
from __future__ import annotations
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from verify_release import RELEASE_FILES, MANIFEST, STATE, WITNESS, audit
from receive_private_review import assess


def run() -> None:
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="f2r-review-smoke-") as tmp:
        root = Path(tmp)
        for rel in RELEASE_FILES - {WITNESS}:
            source = repo / rel
            if not source.is_file():
                raise AssertionError("Public baseline missing: " + rel)
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        config = root / ".streamlit/config.toml"
        config.write_bytes(config.read_bytes() + b"\nenableStaticServing=true\n")
        witness = root / WITNESS
        witness.parent.mkdir(parents=True, exist_ok=True)
        witness.write_text(json.dumps({
            "schema": "F2R_PUBLIC_LIVE_IDENTITY_V1",
            "public_state_sha256": hashlib.sha256((root / STATE).read_bytes()).hexdigest(),
        }), encoding="utf-8")
        manifest = {
            "schema_version":"1.0",
            "system":"Forecast-to-Rank Allocation",
            "files":{rel: hashlib.sha256((root / rel).read_bytes()).hexdigest()
                     for rel in RELEASE_FILES},
        }
        (root / MANIFEST).write_text(json.dumps(manifest),encoding="utf-8")
        result = audit(root)
        assert result["status"] == "F2R_RELEASE_STRICT_VERIFIED"
        bundle = Path(tmp) / "candidate.zip"
        with zipfile.ZipFile(bundle,"x",compression=zipfile.ZIP_DEFLATED) as z:
            for rel in sorted(RELEASE_FILES | {MANIFEST}):
                z.write(root / rel, rel)
        old = (repo/STATE).read_bytes()
        assert assess(bundle,repo,stage=False)
        assert (repo/STATE).read_bytes() == old, "Review unexpectedly rewrote public live state"
    print("F2R_EXISTING_PUBLIC_BASELINE_SYNTHETIC_REVIEW_ROUNDTRIP_PASS")


if __name__=="__main__":
    run()
