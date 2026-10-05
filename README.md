# Kinetix

Kinetix is a production web application for ingesting supplier emails, extracting complete product information from email bodies, preserving PDF catalogues as clickable links without parsing them, and synchronizing structured results to Google Sheets.

## Source of truth

This GitHub repository is the canonical source of truth for implementation, testing, audits, deployment configuration, and release history.

Read these first:

1. `AGENTS.md`
2. `docs/PRODUCTION_HANDOFF.md`

## Non-negotiable product rules

- The brand name **Kinetix** appears only in the primary header/brand area.
- Backend is Python-first and optimized for throughput.
- Scan the complete connected Gmail mailbox.
- Exclude OTPs, security alerts, newsletters, social notifications, promotions, and other irrelevant email from deep extraction.
- Extract all product-related information present in relevant email bodies.
- Support multiple products and dynamic specifications.
- Never infer missing values.
- Never parse/OCR/summarize/index PDF attachments.
- Store PDFs and expose reliable clickable links only.
- Synchronize structured results to Google Sheets.
- Show live progress, throughput, ETA, errors, and review count.
- Preserve source email traceability.
- Use durable idempotent jobs, checkpointing, retries, and deduplication.
- Run full unit, integration, E2E, security, accessibility, and performance audits before release.
- Do not call the project complete until the production deployment is live and smoke-tested.

## Target mailbox

The intended mailbox is `exportdtp@gmail.com`.

Authorization must use Google OAuth. Never request or store the Gmail password.

## Agent workflow

Antigravity or any coding agent should clone this repository, read the production handoff, implement on branches, keep CI green, and only merge/release verified work.

No routine implementation questions are required. Make sound engineering decisions autonomously. Pause only for unavoidable account-owner actions such as OAuth approval, cloud billing approval, or credential entry that cannot be automated.
