# AGENTS.md — Kinetix autonomous implementation contract

You are responsible for delivering Kinetix as a production-ready deployed application.

## Operating mode

- Work autonomously.
- Do not stop at plans or mockups.
- Do not ask routine implementation questions.
- Make reasonable technical decisions and continue.
- Use GitHub as the source of truth.
- Commit coherent changes with descriptive messages.
- Keep tests and CI green.
- Never commit secrets.
- Do not claim completion until production smoke tests pass.

## Required implementation

Read `docs/PRODUCTION_HANDOFF.md` in full before modifying the system.

Priority order:

1. Secure Google OAuth and Gmail ingestion.
2. Fast inbox classification and irrelevant-email exclusion.
3. Complete email-body product extraction with dynamic attributes.
4. PDF store-and-link-only guardrail.
5. Durable persistence, retries, checkpointing, and idempotency.
6. Google Sheets batch synchronization.
7. Professional simple dashboard and search UX.
8. Live progress/ETA.
9. Review queue for ambiguity.
10. Production observability, security, tests, audits, and deployment.

## PDF absolute prohibition

PDF content must never be used as an extraction source. Never OCR, parse text, summarize, vectorize, embed, or send PDF contents to an LLM.

## Branding

Use “Kinetix” only in the primary header/brand position.

## Release gate

Before release, run linting, typing, unit tests, integration tests, E2E tests, browser QA, accessibility checks, security scanning, dependency scanning, secret scanning, and load/performance testing. Fix reproducible defects and rerun affected suites.

The release is done only when the live production URL passes smoke tests.
