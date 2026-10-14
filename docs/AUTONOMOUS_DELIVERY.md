# Antigravity: autonomous end-to-end production delivery mandate

**Owner instruction: Execute the entire Kinetix project end-to-end. User involvement should be limited to truly unavoidable owner-only actions.**

This directive supplements `AGENTS.md`, `docs/PRODUCTION_HANDOFF.md`, and GitHub Issue #1. It does not relax any product or security requirement. The *actual deployed production URL* is the mandatory final deliverable.

## Start here, in the existing project

1. Open the existing local clone of `sanjay-078/Kinetix`; do not create a competing repo or duplicate application.
2. Inspect git status, committed code, frontend/backend, database/migrations, Render configuration, current deployments, tests and CI runs. Identify what is demonstrably implemented versus merely documented.
3. Read all project requirements, GitHub Issue #1 and every comment, especially the genuine Originkit Gency UI directive.
4. Continue implementation immediately. Treat this mandate as an instruction to act, not as a request for yet another plan or permission.

## Autonomous responsibility

Own and complete each workstream:
- Download the **real** Originkit "Welcome to Gency" template with its CLI, inspect what was extracted, run the original files locally, and integrate its genuine frontend design with the existing Kinetix application. Preserve licensed original template assets and code as allowed. Do not fabricate a lookalike. Keep "Kinetix" only in the main header.
- Finish the high-performance Python backend, secure Gmail OAuth, full historical import, incremental sync, irrelevant-email filtering, comprehensive product and arbitrary attribute extraction, multi-product handling, source traceability, review cases, and persistence.
- Preserve PDF attachments **without ever OCRing, parsing, summarizing, embedding, or extracting their content**. Provide reliable links to originals only.
- Finish Drive PDF storage, Google Sheets batch/idempotent export, live processing metrics and genuine ETA, durable jobs/retries/resume/deduplication, search, all dashboard pages, responsive UX, and user-safe observability.
- Fix current product defects and regressions (including any dummy OAuth credentials), configure secrets in production (without ever committing them), and integrate production database, workers, queue and deployment.
- Implement and execute lint, types, unit, integration, E2E, PDF guardrail, security, accessibility, responsive visual, and performance testing. Fix reproducible issues, rerun, and verify actual deployed behavior.
- Keep GitHub updated using coherent commits; keep CI green; deploy to the appropriate persistent HTTPS production service and smoke-test the live URL.
- Record test evidence, deployment proof and unavoidable remaining external restrictions, not unsupported claims of being "verified" or "production ready."

## Self-service troubleshooting before asking the user

Do not treat routine tooling failures as an excuse to halt the project:
- If `gcloud` is not installed, use supported Cloud SDK installation or authenticated Google Cloud APIs/service controls when appropriate; use a browser session if available.
- If Playwright fails to download, repair the pinned package/driver mismatch or use a compatible installed browser, alternate channel, supported build environment, or CI-hosted browser tests. Do not claim browser QA passed if it was never run.
- If registry/CDN access fails, test legitimate mirrors/proxy/settings or an authorized build environment. Never silently replace licensed template assets with guessed code.
- If Render CLI/SDK is unavailable, use the available Render console, connector/API, or authenticated deployment configuration.
- If OAuth credentials or paid template access are absent, complete all other independent tasks while preparing the exact minimal owner step.
- If a process or worker crashes, debug and resume rather than abandoning extraction or claiming success.

## User-only action protocol — strict

The user should **not** have to run shell commands, install tooling, edit source files, debug CI, move secrets between project files, design UI, create deployments manually, choose libraries, click routine setup screens, or fix app errors.

Pause only when an action actually requires owner authorization or manual intervention that your authenticated tools cannot lawfully/technically perform, such as:
- Google / GitHub / Render login or multi-factor authentication;
- approving Gmail OAuth permissions for `exportdtp@gmail.com`;
- creating/approving an OAuth client or managing an OAuth consent screen when programmatic access is unavailable;
- granting access to a cloud project/repository or authorizing billing / new paid spend;
- obtaining a paid licensed Originkit asset / rotating its exposed API key, or accepting vendor terms.

For each unavoidable step, provide exactly:
1. **Why it cannot be performed by the agent** and which alternatives were tried;
2. **One minimal user action**, with direct destination, exact field values and click-by-click instructions;
3. **What the agent will automatically resume** afterward;
4. Explicit instruction **not to paste passwords, OAuth client secrets, or API tokens into chat or GitHub**.

Group related owner-only actions when possible. Do not ask speculative questions. Do not misrepresent software operations as needing user intervention merely because a convenient tool is unavailable.

Never bypass provider consent/security controls or attempt unapproved payment, destructive actions, mailbox deletion, credential sharing, or broad permissions to unrelated projects. Use minimum scoped access.

## Known project anchors — verify rather than assume

- GitHub: `https://github.com/sanjay-078/Kinetix` (private)
- Gmail account intended for connection: `exportdtp@gmail.com`
- Dedicated Google Cloud project ID: `kinetix-510817`
- Previously proposed Render origin: `https://kinetix.onrender.com`
- Previously proposed production OAuth callback: `https://kinetix.onrender.com/api/auth/callback`

Confirm the actual deployed URLs/callback paths in the current source and hosting configuration before making provider settings.

The Originkit API credential has been exposed in a user conversation. Request rotation through an owner-only secure procedure; never reuse/expose that value in GitHub, logs, issue comments, or frontend bundles.

## Operational workflow

- Maintain a concise task checklist in the repo/issue, but **do the work**; do not turn this into endless planning.
- Work through the full implementation and verification with the fewest owner interruptions possible.
- Preserve existing functioning code/data; test migrations; avoid destructive production DB changes without adequate backup/explicit approval.
- Never claim connection or extraction succeeded when OAuth has not completed or real supplier data has not been processed.
- Do not claim browser/CI/performance/security audits succeeded without run evidence.
- For real mailbox operations, protect supplier/private data and minimize scopes.

## Definition of done

Only close GitHub Issue #1 and declare complete after:
- genuine Gency-derived Kinetix UI is functional and deployed;
- persistent HTTPS production site, backend, database, workers and integrations are running;
- real Gmail OAuth is connected to the intended mailbox (or **clearly labeled Awaiting owner OAuth**, in which case the full project is **not complete**);
- full-mailbox ingestion and irrelevant-message skipping are operational;
- all email-body product specifications, variants, pricing and provenance are preserved;
- PDFs are links-only and open the correct originals;
- Google Sheets export is connected, tested and idempotent;
- live progress/ETA is grounded in real metrics;
- test suites/CI, browser E2E, audits and performance checks are evidenced; defects fixed;
- live production site has passed complete smoke tests.

Final report must provide:
**production URL; commit SHA/release; backend/worker/DB status; Gmail and Sheets connection state; historical sync status; live counts; tests/audits with actual results; known issues; owner-only unresolved steps, if any.**

Do not provide a pretend URL or mark a partial deployment production ready.
