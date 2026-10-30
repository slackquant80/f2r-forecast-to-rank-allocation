# Forecast-to-Rank — hosted Streamlit/public artifact governance

**Scope profile:** `DOWNSTREAM_PUBLICATION`. This repository owns the F2R **reviewed public dashboard/Streamlit artifact**, not the canonical F2R strategy model, its private research data or its live Windows computation.

## Canonical ownership and required checks

1. Review this repository's `README.md`, `release_manifest.json`, existing `ci/verify_release.py`, `ci/receive_private_review.py`, `ci/verify_live_witness.py`, and bounded `.github/workflows/f2r-*.yml` contracts.
2. The private strategy source owner is `slackquant80/research-multiasset`; scientific design, forecast-origin timing, point-in-time features, Top-4 ranking/equal weights, next-period execution, costs and private data remain upstream. This public code must not silently recompute or redefine them.
3. When authorized, consult the latest private central `slackquant80/research-governance/main` rules: `AGENTS.md`, `00_CURRENT/UNIVERSAL_GITHUB_PROJECT_GOVERNANCE.md`, `GITHUB_PROJECT_SCOPE_REGISTRY_v1.json`, `00_CURRENT/GIT_EXECUTION_TOPOLOGY_AND_OPERATING_HANDOFF_v1.md`, `00_CURRENT/GITHUB_ZERO_ADDITIONAL_SPEND_POLICY.md`, and applicable rights/publication/clock policy. A public pointer does **not** load or expose private policy or grant cross-repo GitHub Actions permissions.

## Non-negotiable release separation

- A reviewed immutable, rights-safe, source/clock-bound candidate is received only through the current authorized GitHub App/private prerelease route. Do not use a PAT fallback, arbitrary ZIP, legacy local deployment checkout, direct publish or unbounded public-main push.
- A successful source commit or Draft PR does **not** mean the live Streamlit service serves that version. Reconcile exact candidate and manifest, full PR integrity review, human-approved merge, hosted live-witness identity and reader-visible data freshness separately.
- Preserve old historical evidence and explicit completed/current-performance clocks. No copy of licensed/raw data, secrets, internal workstation paths, or private model parameters into the public repository.
- No new service, subscription, quota overage, GitHub Action, automatic deployment, app restart, `main` merge or data publication without separate approval. `GIT-COST-001`: **zero additional spend**.
- Report Pull, Push, any local experiment, Windows operating install, GitHub review candidate, live Streamlit deployment/witness, and retained private evidence as independent states.

**Review-only guidance:** this file neither alters the validated F2R allocation strategy nor asserts that its original local operating source was updated.
