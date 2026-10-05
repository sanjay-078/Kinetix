# Production Handoff

## Mission

Build, test, audit, fix, deploy, and verify Kinetix as a production-ready web application. Do not stop at a prototype, mockup, or implementation plan. GitHub is the source of truth.

The intended Gmail account is `exportdtp@gmail.com`. Google OAuth approval must be completed by the account owner; never request or store the Gmail password.

## User experience

Keep the normal frontend extremely simple, polished, professional, responsive, and suitable for non-technical daily use. Backend complexity must stay hidden from ordinary users.

Use the word **Kinetix only in the primary header/brand area**. Do not repeat it in page titles, cards, buttons, or section labels.

Primary navigation:
- Dashboard
- Products
- Suppliers
- Emails
- Catalogues
- Review
- Integrations
- Settings

The everyday user should mainly:
1. connect Gmail,
2. let processing run,
3. search/filter products and suppliers,
4. open source emails or catalogue PDFs,
5. sync/open Google Sheets,
6. review only ambiguous cases.

## Preferred architecture

Use a production-grade architecture with a Python-first backend.

Preferred baseline:
- Frontend: React/Next.js + TypeScript
- Backend: Python 3.12+ + FastAPI
- Database: PostgreSQL
- Durable worker/queue architecture for mailbox processing
- Redis or managed equivalent when useful
- Realtime progress with SSE or WebSockets
- Google OAuth 2.0
- Gmail API, Google Drive API, Google Sheets API
- Pydantic validation
- secure managed secrets
- production hosting independent of a developer laptop

Use another architecture only if it is clearly superior in the available environment while preserving all requirements.

## Gmail connection and full mailbox import

Provide a simple **Connect Email** flow using Google OAuth.

On first connection:
- discover and scan the entire mailbox history,
- use Gmail API pagination and batching,
- use async I/O and bounded concurrency,
- checkpoint progress,
- retry transient failures with exponential backoff and jitter,
- persist Gmail message/thread identifiers for idempotency,
- resume after crashes/restarts rather than restarting,
- prevent duplicate processing.

After historical import, switch to incremental synchronization for new or changed messages.

## Fast irrelevant-email elimination

Every email must be classified before expensive extraction.

Quickly exclude from deep extraction:
- Instagram/social OTPs and verification mail,
- Google security alerts,
- Claude or other service verification mail,
- login codes,
- automated account alerts,
- newsletters,
- promotional/marketing mail,
- unrelated receipts,
- spam,
- other clearly non-product automated messages.

Use fast Python-first signals:
- sender/domain,
- subject,
- headers,
- auto-generated markers,
- OTP/security-code patterns,
- unsubscribe/newsletter signals,
- lightweight body features,
- previously learned sender/domain classification.

Do not physically delete Gmail messages by default. “Eradicate” means mark ignored/non-supplier in Kinetix and never waste deep extraction on them again.

Do not rely only on hardcoded domains. If classification is uncertain, perform a second lightweight check. If still uncertain, preserve it for deeper analysis rather than losing supplier data.

Cache sender/domain classifications for speed.

## Complete product extraction

For every relevant supplier/product email, extract **all product-related information contained in the email body**.

Capture whenever present:
- product name/title/category,
- brand/manufacturer,
- model/model number,
- part number/SKU,
- series/variant/version,
- description,
- quotation reference,
- quantity/available quantity/MOQ/unit,
- unit price/tier price/total price/currency,
- discounts/taxes/shipping/tooling/sample price,
- dimensions/diameter/weight,
- material/grade/finish/color,
- capacity/voltage/current/power/wattage/frequency,
- speed/RPM/pressure/temperature/tolerance,
- performance data/IP rating/noise level,
- certifications/compliance/compatibility,
- packaging/carton quantity/gross/net weight,
- country of origin/HS code,
- warranty/lead time/production time,
- shipping terms/Incoterms/payment terms,
- quotation validity/customization/sample availability,
- contact information,
- any other technical or commercial product attribute in the email.

Never discard an attribute merely because no fixed database column exists.

Use a hybrid data model:
- normalized common fields on product records,
- dynamic structured key/value/unit attributes,
- normalized attribute table for querying.

Never hallucinate or infer missing values. Preserve original wording and units. Missing values remain null/blank/not provided.

Retain source traceability for extracted values to the originating email and, when practical, an evidence snippet/section.

## Multiple products in one email

An email may contain one product or hundreds.

Create separate product/variant records where appropriate and correctly associate:
- model,
- SKU,
- price,
- quantity,
- specification set,
- commercial terms.

Do not flatten many products into one unstructured cell.

Shared email-level commercial terms may be stored once and related to all applicable products.

## Maximum-speed extraction strategy

Use Python deterministic extraction before AI wherever possible:
- HTML tables,
- plaintext tables,
- key/value labels,
- regex,
- price/currency detection,
- model/SKU patterns,
- units/measurements,
- quantities,
- quotation structures,
- signature/contact parsing.

Use an AI extraction layer only for complex or ambiguous unstructured language.

Use strict structured outputs and validate AI output in Python before persistence.

Parallelize safely and batch where supported. Optimize for throughput without provoking quota failures.

## Ambiguity and review

Never silently guess.

Create a **Needs Review** record for unclear mappings, conflicting values, multiple currencies, incomplete tables, or similar uncertainty.

Review UI should show:
- source email,
- candidate extracted values,
- reason for uncertainty,
- confidence,
- editable fields,
- confirm/save,
- retry extraction.

Do not require approval for normal high-confidence extraction.

## PDF absolute rule

PDF attachments must NEVER be parsed for product information.

For every PDF:
1. detect it,
2. download original bytes,
3. preserve filename,
4. validate file type/signature,
5. store/upload to a dedicated Google Drive folder or approved persistent storage,
6. create a stable clickable link,
7. associate it with source email and related supplier/products,
8. stop.

Never:
- OCR a PDF,
- extract PDF text,
- parse PDF tables,
- summarize a PDF,
- vectorize/embed a PDF,
- send PDF content to an LLM,
- inspect catalogue pages for specifications.

End-to-end tests must prove the PDF is stored and opens correctly, while no PDF content enters extraction.

## Data model

At minimum use durable entities for:
- connected_accounts,
- mailbox_sync_state,
- emails,
- suppliers,
- products,
- product_attributes,
- email_product_relations,
- attachments,
- pdf_links,
- extraction_runs,
- extraction_issues,
- review_items,
- sheet_sync_state,
- processing_jobs,
- audit_events.

Use stable IDs, foreign keys, hashes/idempotency keys, Gmail IDs, and indexes required for high-volume queries.

## Dashboard and live ETA

Main dashboard should show simple cards:
- Products
- Suppliers
- Emails Processed
- Catalogues
- Needs Review

Show live processing:
- total emails discovered,
- emails scanned,
- irrelevant emails ignored,
- supplier emails identified,
- supplier emails fully processed,
- products extracted,
- PDFs stored,
- failures/retries,
- current processing speed,
- elapsed time,
- estimated remaining time,
- estimated completion time,
- percentage complete,
- plain-language status.

Do not fake ETA. Compute it continuously from recent rolling throughput and remaining work, smoothing short spikes. API throttling must naturally change the ETA.

Use user-facing labels such as:
- Processing normally
- Waiting to process
- Temporarily slowing down — processing will continue automatically
- 1 email could not be processed — Retry

Hide worker internals and stack traces from the normal UI.

## Products, suppliers, emails, catalogues

### Products
Fast search/filter over product name, model, SKU, supplier, category, price/currency, attributes, and date.

Product detail must show:
- product identity,
- supplier,
- price/MOQ,
- normalized and dynamic specifications,
- commercial details,
- catalogue links,
- source email link,
- received date,
- review/confidence state when relevant.

### Suppliers
Supplier profile should show contact/domain, product count, email count, catalogue count, recent communication, recent products, and related records.

Merge supplier identities carefully. Do not merge ambiguous organizations without evidence.

### Emails
Not a Gmail clone. Use for traceability:
- supplier/sender/subject/date,
- classification,
- extraction status,
- products found,
- PDF count,
- source email link.

### Catalogues
Searchable document library:
- filename,
- supplier,
- source email,
- received date,
- open PDF action.

No catalogue content extraction or summary.

## Google Sheets

Provide simple connect/select spreadsheet UI.

Use batch writes, never cell-by-cell loops.

Maintain at least:
### Products
One row per product/variant with stable Product ID, common searchable fields, and an Additional Specifications field when needed.

### Emails
Email ID, sender, supplier, subject, date, classification, status, source email link.

### Attachments
Attachment ID, supplier, email ID, filename, MIME type, PDF link, received date.

Optional Attributes tab:
Product ID, attribute, value, unit, source email ID.

Synchronization must be idempotent: reruns update rows rather than duplicate them.

## Performance and reliability

Use:
- async I/O,
- connection reuse,
- bounded concurrency,
- batching,
- bulk DB upserts,
- indexes,
- caching,
- durable queues,
- checkpointing,
- idempotent jobs,
- exponential backoff + jitter,
- dead-letter/retry handling,
- rate-limit awareness.

The system must survive:
- deployment/process restart,
- network interruption,
- Gmail 429/quota throttling,
- temporary Google API failures,
- database reconnects,
- malformed/huge emails,
- duplicates,
- partially processed messages,
- Sheets/Drive failures.

No email may be lost because a worker crashes. Retries must not duplicate products.

## Security and privacy

Required:
- encrypted OAuth tokens at rest,
- least-privilege scopes,
- HTTPS,
- secure cookies,
- CSRF controls,
- CSP,
- safe rendering of email content,
- never render raw untrusted HTML,
- SQL injection protection,
- input validation,
- app rate limiting,
- redacted logs,
- safe attachment filenames,
- file size limits,
- PDF MIME/signature validation,
- audit trail,
- logout/token revocation,
- dependency vulnerability scanning,
- secret scanning,
- no secrets committed to Git.

Do not send ignored OTP/security emails to an AI model. Never send PDF content to any model.

## Observability

Add production metrics/logging for ingestion rate, classification rate, extraction latency, AI latency, errors, retries, Gmail throttling, Drive failures, Sheets failures, DB latency, queue depth, active workers, and review rate.

Provide optional admin diagnostics separate from the normal UI.

## Test requirements

Before production, create and pass:

### Unit
classification rules, OTP/newsletter detection, sender/domain cache, price/currency parsing, model/SKU extraction, unit parsing, dynamic attributes, idempotency, ETA, sheet rows, PDF guardrails.

### Integration
Gmail pagination/fetch, MIME parsing, Drive PDF storage, Sheets batch sync, DB persistence, retry/backoff, checkpoint resume, OAuth refresh.

### Extraction fixtures
plaintext/HTML quotations, HTML tables, multiple products, multiple currencies, tier pricing, “respectively” text, missing fields, unusual model numbers/specifications, forwarded threads, signatures, OTPs, newsletters, automated notifications.

### PDF guardrail
prove PDF is downloaded, stored, linkable, byte-preserved where applicable, never parsed/OCRed/sent to LLM, and opens correctly.

### End-to-end
connect Gmail, historical sync, irrelevant-email filtering, product extraction, multi-product email, dynamic attributes, PDF link, product traceability, Sheets sync, worker restart/resume, deduplication, review workflow.

### UI/UX
desktop/tablet/mobile, loading/empty/error states, accessibility, keyboard use, screen-reader labels, responsive tables, long values.

### Performance
large synthetic mailbox fixtures, messages/min, extraction throughput, DB writes, Sheets throughput, quota behavior, worker scaling.

### Security
dependency scan, static analysis, secret scan, auth/session/OAuth review, XSS/SQLi/CSRF/upload/access-control checks.

## Audit loop

Repeat until release criteria are met:
1. build,
2. lint/typecheck,
3. unit tests,
4. integration tests,
5. E2E tests,
6. browser QA,
7. accessibility audit,
8. security audit,
9. performance audit,
10. inspect logs,
11. fix reproducible bugs,
12. rerun affected suites.

Do not knowingly deploy critical/high-severity defects.

## Production release criteria

The project is complete only when:
- production URL is live,
- polished responsive UI works,
- Gmail OAuth is configured,
- owner can authorize `exportdtp@gmail.com`,
- entire mailbox history imports,
- irrelevant email is efficiently excluded,
- relevant email product data is preserved completely,
- multiple products are handled,
- PDFs are linked and never parsed,
- Google Sheets sync works,
- live progress/ETA works,
- retries/checkpointing/idempotency work,
- review flow works,
- tests pass,
- no unresolved critical/high security issue,
- performance is acceptable,
- production smoke test passes,
- known issues are documented,
- deployment URL is provided.

## Autonomy

Do not ask the user about normal engineering choices such as libraries, folders, indexes, queue technology, tests, retries, pagination, caching, deployment layout, breakpoints, or routine bug fixes. Choose good defaults and proceed.

Only stop for a genuinely unavoidable account-owner action such as Google OAuth consent, cloud billing/permission approval, or a credential that software cannot create itself.

When blocked, complete everything else first and request exactly the one required action.
