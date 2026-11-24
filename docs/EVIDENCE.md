# Verification evidence

Review baseline: `9b7dbf2` on `main`. Verified locally on 24 November 2026.

| Check | Observed result |
|---|---|
| Full pytest suite, including golden regression | **83 passed**, 44.48 seconds |
| Branch-aware coverage | **98.56%**, batch entrypoint excluded |
| Ruff | Passed for source, tests and golden checker |
| Mypy | Passed: 16 source files |
| Import contract | 1 kept, 0 broken |
| Batch command and strict golden checker | **5,000/5,000** scores matched; 13.28 seconds for batch |
| Deliberate original bug (`hour <= 6`) | `test_night_flag_boundaries[6-0]` failed as intended; source restored |
| Local Docker image | **544,893,152 bytes** reported by `docker image inspect`, Linux ARM64 |
| Container readiness and prediction | HTTP success; score **0.62614**, decision `allow`, version `v3.2.0` |
| Golden comparison inside the slim container | **5,000/5,000** matched; batch 24.67 seconds |
| Container identity | `appuser` |
| Gitleaks 8.30.1, repository history including fixes | 11 commits scanned; no leaks found |

Local pytest emitted a sandbox physical-CPU discovery warning and fell back to logical cores. No test failed. Local ARM64 image size is not a substitute for CI's AMD64 measurement: CI separately enforces the 600,000,000-byte cap.

The old `BENCHMARKS.md` figures are historical. Its Docker disk-usage and content-size columns use different storage measures and should not be compared directly with each other.

## Reproduce

```bash
make lint
make test
make golden
docker build -t raqib:verify .
docker image inspect raqib:verify --format '{{.Size}}'
docker run --rm raqib:verify whoami
pre-commit run --all-files
```

The full golden test now runs on every PR as well as nightly. Runtime dependency resolution in CI is constrained by `requirements.lock`.

## Repository settings

These are owner-level settings, not files, and have **not** been changed by this PR.

1. In GitHub Settings → Branches / Rulesets, protect `main`.
2. Require a pull request and successful `lint`, `test`, `secrets`, `image-smoke` checks. For individual work, do not require self-approval.
3. Block force pushes and deletions; ensure the rule is enforced for the owner too.
4. Enable GitHub secret scanning / push protection where available.
5. After protection is active, open a temporary PR with the original boundary bug. Capture the blocked merge state, repair the bug without weakening tests, and retain the link/screenshot as evidence.
6. Verify the published GHCR package can be pulled with the intended permissions.

A locally demonstrated failing test is **not** evidence that GitHub blocks merging. The blocked-PR screenshot remains pending until these settings are active.

## Submission scope

Jana confirmed that the instructor approved Raqib itself as the individual final submission. The personal stage entries in `JOURNAL.md` require the author's own observations and explanation; they are intentionally not fabricated.
