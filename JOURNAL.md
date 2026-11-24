# Individual project journal — Jana Alhumaizi

The instructor approved Raqib as Jana’s individual final submission, as confirmed by Jana. This journal separates verified implementation from the author's personal learning record. No historical actions or understanding are invented.

## Scope

Current repository: workshop fraud service using synthetic data. This is the instructor-approved individual final submission.

## Engineering review and hardening · 24 November 2026

**Request:** fix the review findings, improve presentation and keep the work concise.

**Built:** strict complete golden-output checks; UTC-aware timestamps; recursive structured-secret masking; safe exception events; error trace headers; smaller runtime dependencies; full golden CI; secret scanning; image-size gate; Makefile; clearer README.

**Verification:** see [EVIDENCE.md](docs/EVIDENCE.md) for commands and actual results.

**Why these changes matter:** a green check must not accept missing predictions. Equivalent timestamps should produce the same features. Secrets inside nested log fields need masking too. A release should carry enough evidence for another person to reproduce it.

## Learning record — author to complete

For each stage, record your own explanation, what you asked the agent, the command you ran and what you observed. Link evidence rather than copying an expected result.

| Stage | Author's explanation and observations |
|---|---|
| 0 · Model, baseline and limitations | Pending author entry |
| 1 · Architecture and golden comparison | Pending author entry |
| 2 · API and invalid requests | Pending author entry |
| 3 · Container and dependencies | Pending author entry |
| 4 · Tests and deliberate regression | Pending author entry |
| 5 · Pipeline and blocked PR | Pending author entry; protection setup pending |
| 6 · Secrets and incident response | Pending author entry |

## Walkthrough prompts

1. Which file changes if the model library changes?
2. Why does a matching golden file not establish real-world accuracy?
3. How do health and readiness differ?
4. Which test catches the original 06:00 boundary bug?
5. What prevents a failing PR from merging?
6. What is the first action after a credential leaks?
