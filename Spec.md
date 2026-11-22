# CivicFlow AI — Product & Technical Specification

**Version:** 1.0 · **Date:** 22 November 2026 · **Status:** Hackathon MVP specification  
**Chosen track/problem:** Track 1 — Civic Pulse, Digital Governance & Public Information; Transparent Civic Grievance & Infrastructure Triage System.

## 1. Project overview

CivicFlow AI is a lightweight civic-issue intelligence prototype. It receives citizen reports about public infrastructure, converts unstructured descriptions into structured records, looks for potentially related submissions, assigns an explainable triage priority, recommends an operational next step, and exposes report status to the citizen through a reference ID.

The product is deliberately not a government grievance portal. It does not transmit data to a city authority or claim official resolution. The MVP simulates the citizen-to-authority workflow locally so that its product logic can be demonstrated safely.

## 2. Problem statement

Citizens encounter damaged roads, potholes, overflowing waste, drainage failures, broken streetlights, and unsafe pedestrian routes. Reports can arrive through multiple channels and in inconsistent language. A team reviewing such reports can spend time interpreting descriptions, deciding categories, identifying repeat reports, assessing urgency, and determining the next action. Treating every report as a separate task can obscure the size and location of an underlying issue.

**Who faces the problem:** citizens who need to report neighborhood infrastructure issues, and civic operations teams who need to understand and organize incoming reports.  
**Why it matters:** weakly structured reports and fragmented issue context can make it harder to notice repeated reports, explain why a case needs attention, and communicate progress.

## 3. Target users and stakeholders

- **Citizen / reporter:** supplies a location and plain-language issue description, optionally attaches a photo, receives a ticket ID, and checks status.
- **Authority / operations reviewer (simulated):** reviews the queue, sees category, priority reasons, related-report count, and a suggested next action, and updates status.
- **Hackathon judge / evaluator:** observes the complete workflow and can distinguish live LLM assessment from fallback logic.
- **Future municipal partner (out of MVP):** would define trusted department mappings, governance rules, integrations, retention policies, and operational service levels.

## 4. Existing solution analysis

Research reviewed on 22 November 2026:

| Product / initiative | Existing capability evidenced by product material | Implication for CivicFlow |
|---|---|---|
| FixMyStreet (mySociety) | Reports are sent to the body responsible using location/category; reports are visible, people can see prior reports, post updates or subscribe, and duplicate reports are considered. [How it works](https://fixmystreet.org/how-it-works/) | Routing, public visibility, and duplicate avoidance are established product patterns, not a novel claim for CivicFlow. |
| SeeClickFix / CivicPlus | Product documentation describes AI-improved category search and photo analysis, duplicate marking/merging, request prioritization, status changes, assignment, and request search. [Request management documentation](https://www.civicplus.help/seeclickfix/docs/request-management) | AI categorization and duplicate operations also exist commercially. CivicFlow must show its own end-to-end issue-level triage clearly rather than claim these capabilities are unprecedented. |
| Swachhata Platform (MoHUA / Swachh Bharat Mission Urban) | Citizens can submit a photo; the app can identify location from photo geolocation, forward a complaint to the municipal corporation, and provide status updates. [Platform overview](https://dashboard.swachh.city/) | Photo/location submission and status tracking already exist in the Indian civic context. |
| UPYOG Public Grievance Redressal (NIUA) | PGR describes complaint routing to municipal departments, GIS location mapping, status tracking, dashboards, auto-escalations and SLAs. [PGR overview](https://upyog.niua.in/homepage/public-grievance-redressal/) | A dashboard and departmental workflow are not sufficient differentiation on their own. |
| I Change My City (Janaagraha) | App listing describes photo-based complaints, map location selection, agency routing and follow-up. [Google Play listing](https://play.google.com/store/apps/details?id=com.ichangemycityjanaagraha.core) | Citizen participation and agency routing are existing patterns. |

**What established systems do well:** convenient reporting, location/category selection, routing, reference/status tracking, authority work queues, and in some systems duplicate handling, maps, notifications, priority or SLA workflows.

**Potential gaps this MVP explores (not asserted as universal shortcomings of the named products):** a compact view that combines multiple reports into an underlying issue cluster; showing the evidence behind a triage score in plain language; and attaching one actionable recommendation to that cluster while preserving each citizen's reference ID.

## 5. Product gap and opportunity

The project will not compete by reproducing a full 311 or grievance portal. It demonstrates a narrow intelligence layer between intake and operations:

1. Translate free-text reports into structured issue records.
2. Find likely related submissions from the same location/category context.
3. Make priority reasoning inspectable rather than returning an unexplained label.
4. Show the next practical action in the authority view.
5. Keep each citizen report independently trackable even when related reports are grouped.

This is a proposed product focus, not a claim that no existing product offers any of these functions.

## 6. Core innovation and differentiator

**Issue-level intelligence instead of a report-only queue.** CivicFlow's demo groups potentially related reports around one underlying location/category issue, surfaces the number of additional reports, exposes the factors contributing to priority, and provides a recommendation grounded in the submitted text/category.

The tangible judge demonstration is two independently worded pothole reports at the school gate. The authority view shows they may describe one issue, reveals safety evidence and score factors, and offers an inspection / temporary hazard-marking recommendation. Each citizen still uses their own ticket ID to track the report.

## 7. Complete user journey

### Citizen
1. Open the report page.
2. Choose English, Telugu, or Hindi interface labels.
3. Enter an issue location and description; optionally attach a JPG/PNG/WEBP image (maximum 3 MB).
4. Submit the form.
5. Receive a unique `CF-XXXXXXXX` ticket ID and an indication of whether the assessment used a configured LLM or the rules fallback.
6. Open Track Report and enter the ID.
7. See category, current status, priority, suggested department, related-report count, and recommended next step.

### Authority reviewer (simulated)
1. Open Authority Desk.
2. Review total reports, high-priority reports, issue-cluster count and resolved count.
3. Filter the queue by priority and status.
4. Expand a report to inspect score reasons and recommended action.
5. Change status to Received, Under Review, In Progress, or Resolved.
6. The citizen tracking endpoint immediately returns the updated status.

## 8. Feature prioritization (P0 / P1 / P2)

| Priority | Feature | MVP decision |
|---|---|---|
| P0 | Citizen text + location submission | Implemented |
| P0 | Persistent SQLite record and unique reference ID | Implemented |
| P0 | Citizen report tracking | Implemented |
| P0 | Category/severity assessment | Optional LLM with explicitly labelled rules fallback |
| P0 | Explainable priority scoring | Implemented as a transparent heuristic |
| P0 | Related/duplicate candidate detection | Implemented as a lightweight similarity heuristic |
| P0 | Authority queue and status updates | Implemented |
| P0 | Recommended next action | Implemented using category templates / model response |
| P1 | Basic English/Telugu/Hindi interface labels | Implemented for primary workflows |
| P1 | Optional photo evidence upload | Implemented; no automated image analysis |
| P1 | Demo-data seeding / clearing | Implemented, records labelled DEMO |
| P2 | Actual GIS map, coordinates and geospatial clustering | Deferred |
| P2 | Authority login, roles, citizen accounts | Deferred; not safe for live deployment as-is |
| P2 | Real municipal routing, notifications, SLA/escalation, appeals | Deferred |
| P2 | Full multilingual translation / voice submission | Deferred |
| P2 | Duplicate review/merge interface and model evaluation | Deferred |

## 9. Application pages and responsibilities

- **Report an issue:** landing/context statement, location and description fields, optional photo, language choice, privacy reminder, submission confirmation.
- **Track report:** reference ID lookup and status/category/priority/recommendation detail.
- **Authority desk:** compact KPI row, queue filters, issue cards, expandable triage rationale, and status controls; demo-data controls are visibly labelled.

## 10. UI layout and component descriptions

- Top bar: CivicFlow brand, three page navigation buttons, language selector.
- Citizen hero: explains the promise and limits; no unsupported claims about government integration.
- Report panel: location, description, photo, privacy note, submit button, confirmation card.
- Workflow sidebar: report → AI organisation → team prioritisation.
- Boundary notice: explicitly states reports are not sent to a government department and scores are not official.
- Tracking result: reference ID, status, category, priority, team recommendation, related count, and assessment mode.
- Authority desk: metric cards, DEMO banner, filters, prioritized issue cards, details panel and editable status.
- Responsive behavior: single-column mobile layout, scrollable navigation, and stacked queue cards.

## 11. AI processing workflow

1. Validate description and location.
2. If `AI_API_KEY` or `OPENAI_API_KEY` exists, call the configured OpenAI-compatible Chat Completions endpoint with a constrained JSON request. Ask for category, severity (1–5), safety evidence, duration evidence, summary and recommendation. Treat report content as untrusted data.
3. Validate the model category against the supported category list and clamp severity to 1–5.
4. If the key is missing or the request/response fails, run deterministic keyword rules and mark the record `rules_fallback`.
5. Calculate a local explainable priority score using both the structured assessment and explicit text evidence. The model does not set the score directly.
6. Search same-category reports in the same demo/non-demo data partition for candidate location and description overlap.
7. Persist the ticket, assessment mode, score reasons, recommendation and cluster identifier.

The application never labels rule output as live AI. Model-generated recommendations are bounded to the supplied report and should not invent affected-person counts, official decisions or verified causes.

## 12. Priority-scoring methodology

Prototype heuristic, maximum 100:

- Base score: 10.
- Category impact: Road Damage 12; Waste & Sanitation 7; Water & Drainage 10; Streetlight & Electrical 9; Public Safety 12; Other 4.
- Reported severity: severity value (1–5) × 5.
- Safety indicator explicitly detected in the report/model evidence: +25.
- Duration language (e.g. days/weeks/months) detected: +8.
- Additional related reports in the cluster: +5 each, capped at +15.
- Clamp final score to 100.

Priority labels: High ≥65; Medium ≥38; Low <38. The queue sorts High, Medium, Low, then newest. A reason list is saved with every complaint. These weights are illustrative, not calibrated with incident outcomes, and not an official government risk score. The system does not invent an affected-person count.

## 13. Duplicate / related complaint methodology

- Compare only records in the same data partition (demo with demo; non-demo with non-demo).
- Require the same assessed category.
- Tokenize Unicode text, lowercase/casefold, remove a small set of generic location words, then calculate Jaccard overlap for location and description.
- Candidate rule: location overlap ≥0.55 and description overlap ≥0.16, or location overlap ≥0.82 and description overlap ≥0.10.
- Link a candidate to the existing cluster root and count additional reports.
- Do not delete, merge or hide citizen submissions.

**Known weakness:** lexical matching can miss paraphrases, transliteration and geographic proximity expressed with different place names; it can also create false matches. This is a triage hint only. A future version should use geocoding, semantic embeddings, review thresholds, and human confirmation.

## 14. Database schema

Single SQLite `complaints` table:

| Field | Type | Purpose |
|---|---|---|
| id | INTEGER PK | Internal row identity |
| ticket_id | TEXT UNIQUE | Public reference token |
| description | TEXT | Original citizen description |
| original_language | TEXT | `en`, `te`, or `hi` selection |
| location | TEXT | Citizen-entered location text |
| category | TEXT | One supported issue category |
| severity | INTEGER | 1–5 assessment |
| priority | TEXT | High / Medium / Low |
| priority_score | INTEGER | Explainable 0–100 heuristic |
| priority_reasons | TEXT JSON | Saved factor-by-factor rationale |
| department | TEXT | Suggested department label, not a live routing destination |
| recommendation | TEXT | Recommended first action |
| status | TEXT | Received / Under Review / In Progress / Resolved |
| cluster_id | TEXT | Ticket ID of underlying issue cluster root |
| summary | TEXT | One-line summary (model-written, or a word-boundary excerpt in fallback mode); added during implementation |
| ai_mode | TEXT | `llm` or `rules_fallback` |
| image_path | TEXT nullable | Local optional photo path |
| is_demo | INTEGER | Clearly separates synthetic demo records |
| created_at / updated_at | TEXT | UTC ISO timestamps |

Indexes: ticket ID, cluster ID and creation time. Database initializes at application startup. `DATABASE_PATH` can point to a persistent mounted volume.

## 15. API endpoint specifications

| Method | Path | Request | Response / behavior |
|---|---|---|---|
| GET | `/health` | none | Service liveness |
| GET | `/api/config` | none | Reports whether an API key is configured; never returns the key |
| POST | `/api/complaints` | multipart: `description`, `location`, `language`, optional `photo` | Validates and stores complaint; returns ticket and assessment |
| GET | `/api/complaints/{ticket_id}` | reference ID | Returns citizen tracking record and related count; 404 if unknown |
| GET | `/api/admin/complaints` | optional `status`, `priority` query | Returns queue and summary metrics |
| PATCH | `/api/complaints/{ticket_id}/status` | JSON `{ "status": ... }` | Updates one ticket; allowed values are fixed; 404 if unknown |
| POST | `/api/demo/seed` | none | Creates three clearly marked sample reports once |
| DELETE | `/api/demo/clear` | none | Removes only demo records |

All write routes are unauthenticated in this demo. That is a documented limitation, not a production design.

## 16. Technology stack and architecture

- Python 3.10+.
- FastAPI for the HTTP application and request validation.
- Uvicorn for ASGI serving.
- SQLite via Python's standard `sqlite3` module for simple persistent storage.
- Vanilla HTML, CSS and JavaScript for a light responsive frontend.
- Optional OpenAI-compatible HTTP Chat Completions endpoint using Python standard library networking; no SDK required.
- `python-multipart` for optional image upload.

Architecture: browser UI → FastAPI route → assessment / matching / priority service functions → SQLite. The browser polls/requests API results on page actions; no real-time push channel is included.

## 17. Multilingual implementation strategy

- The primary report, tracking and authority labels are localized through separate English, Telugu and Hindi dictionaries in `static/i18n.js` (used by `static/app.js`).
- The language selector is submitted as `en`, `te` or `hi`; original complaint text is stored unchanged.
- The configured LLM receives the language tag and original text, and is instructed to interpret the report while returning structured English operational fields.
- The fallback contains a small set of Telugu/Hindi keywords but is not a full translation or reliable multilingual classifier.
- Voice input, speech output and full translation of dynamic AI content are not in the MVP.

## 18. Error handling and fallback strategy

- Missing/invalid form values → HTTP 422 and actionable message.
- Unsupported photo MIME type → HTTP 415.
- Photo larger than 3 MB → HTTP 413.
- Unknown ticket ID → HTTP 404.
- Invalid status value → request validation error.
- Missing AI key or AI request/response errors → rules-based assessment; save `rules_fallback` visibly.
- Unknown/unavailable category from model → reject model assessment and use fallback.
- SQLite initialization runs on application startup; health endpoint offers a basic process check, not a full dependency health check.

## 19. Security and privacy considerations

- Never commit API keys; inject them as environment variables.
- Ask citizens not to submit names, phone numbers or sensitive personal information.
- Validate description/location lengths and image MIME type/size; generate server-side image names.
- Demo routes and authority status routes are open without authentication. The app is not suitable for real citizen data or public production use until access control, rate limiting, abuse handling and audit trails are added.
- Uploaded images are served from a local static directory in this prototype. A real service must use private object storage, malware/content scanning, access control and a retention/deletion policy.
- The prototype makes no official eligibility, safety clearance, emergency dispatch or government-routing decision. Emergency hazards should be reported through relevant local emergency channels.

## 20. Deployment instructions

Render Web Service example:

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Optional environment: `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`.
- Attach persistent storage for SQLite and set `DATABASE_PATH` to the writable mount path; otherwise redeploys/restarts may discard local data depending on host behavior.
- After deployment verify `/health`, submit a complaint, track it, update status, and track it again from an external browser.

No live deployment is claimed by this specification. Deployment must be separately completed and smoke-tested.

## 21. Environment variables and configuration

| Variable | Required | Default / purpose |
|---|---|---|
| `AI_API_KEY` | No | Optional LLM credential; `OPENAI_API_KEY` is also read |
| `AI_BASE_URL` | No | `https://api.openai.com/v1/chat/completions` |
| `AI_MODEL` | No | `gpt-4o-mini` |
| `DATABASE_PATH` | No | `./civicflow.db` next to app |
| `UPLOAD_DIR` | No | `./uploads`; photo folder (added during implementation) |
| `PORT` | No | `8000` when run directly |

The `.env.example` is documentation only; the application does not automatically parse `.env` files. In production, set values in the host environment.

## 22. Testing and acceptance criteria

### Local smoke tests

1. `GET /health` returns `{"status":"ok","service":"CivicFlow AI"}`.
2. Submit a report without API credentials; response includes a ticket ID and `ai_mode=rules_fallback`.
3. Retrieve the report using the ID; description, location and status are preserved.
4. Submit a second similar report at the same location/category; related count is greater than zero.
5. Open the admin queue; counts and report records appear.
6. Change a ticket to `In Progress`; tracking endpoint returns the new status.
7. Load demo data; two similar school-gate pothole reports are grouped and all sample rows are marked DEMO.
8. Clear demo data; non-demo records remain.
9. Upload an acceptable image and reject unsupported/oversized files.
10. Use the English, Telugu and Hindi interface selectors; core labels change and report content remains intact.

### Acceptance criteria

- End-to-end report → stored ticket → authority triage → status update → citizen tracking works locally.
- AI mode is never misrepresented; fallback is explicit.
- Priority reasoning is visible and includes the non-official-score disclaimer.
- The duplicate match is described as possible/related, not as a confirmed duplicate.
- The UI explicitly explains no government connection exists.
- No API secret is included in frontend code or source control.

## 23. Known MVP limitations and future improvements

- No citizen or authority authentication / authorization.
- No actual municipal integrations, assignment notifications, SMS/WhatsApp/email, appeals, escalation or SLA timers.
- No coordinates, map, geospatial distance, ward boundaries or authority directory.
- Text-token similarity only; needs evaluation with representative multilingual data and human review.
- Heuristic priority has no field calibration or fairness/safety validation.
- No AI photo understanding despite optional photo storage.
- Telugu/Hindi interface strings are partial; fallback multilingual recognition is limited.
- Local photo/database storage needs production-grade persistent and private storage.
- Next increments: human-confirmed cluster review; geospatial + semantic similarity; ward/department directory; secure roles; photo evidence workflow; notifications; full localization; audit history; calibrated triage model.

## 24. Judge demo scenario

**Scenario:** Two residents independently report a dangerous pothole by a school gate in Banjara Hills. A separate overflowing-garbage report illustrates category separation.

1. In Authority Desk, click Load demo scenario.
2. Show the two separate pothole reports grouped as one underlying issue; show an additional report count.
3. Expand triage reasoning: show category impact, severity, safety indicator, duration evidence and related-report factor.
4. Point to the suggested first action (field inspection and hazard marking if a risk is confirmed).
5. Copy a pothole ticket ID and open Track Report.
6. Change that ticket status in Authority Desk to In Progress.
7. Return to Track Report and retrieve the same ID; the updated state is visible.
8. Explain that each citizen retains an individual ticket while operations can see a likely shared issue. State that this is a local simulation, not a live municipality integration.

**60–90 second narrative:** “A normal grievance portal stores a complaint. CivicFlow tries to help an operations team understand the issue behind multiple complaints. It structures the text, detects possible related reports, explains why the issue is prioritized, and suggests a next action. The citizen can still track their own reference. In this prototype, AI is used only when configured; otherwise we clearly show the rules fallback. Nothing is sent to a government department.”

## 25. Implementation notes (added after the build, 22 November 2026)

Decisions made while implementing the MVP where the specification was silent or needed a small addition:

- **Extra column and variable:** `summary` column and `UPLOAD_DIR` variable, as marked in sections 14 and 21. Photos are served by a validated `/uploads/{name}` route rather than a static mount.
- **Photo checks:** the file type is identified from its leading bytes, not only the client-supplied MIME type; a mismatched or unknown file returns 415.
- **Cluster recount:** when a new report joins a cluster, every earlier member is re-scored so the related-reports factor stays consistent. Existing reports are never merged or hidden.
- **KPI definition:** "issue clusters" counts clusters containing two or more reports.
- **Queue order:** High, Medium, Low, then newest; within one priority the score does not break ties.
- **Demo seeding** always uses the rules assessment so the scenario is reproducible, even when an AI key is configured; those records are stored and labelled `rules_fallback`.
- **Demo reports** are worded briefly, like real citizen reports. The matching thresholds in section 13 are unchanged. Long, differently worded reports can share too few words to be grouped, which is the weakness section 13 already names.
- **LLM failure handling:** network errors, HTTP errors, malformed JSON, an unsupported category or a missing recommendation all trigger the labelled fallback. One retry without `response_format` is made on HTTP 400/422.
- **Language of dynamic content:** department names, recommendations and score-reason details are shown in English in all three interfaces.
- **Fonts:** the page requests Barlow Condensed, Public Sans and Noto Sans Telugu/Devanagari from Google Fonts, with system fallbacks if the request is blocked.