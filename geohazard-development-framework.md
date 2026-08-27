# GeoHazard PH — Development Framework & Methodology

*Companion to `geohazard-system-architecture.md` — this document covers how the project gets built, not what gets built.*

---

## 1. Methodology: Agile (Scrum-lite)

Full Scrum ceremonies are overkill for a small team, but the core rhythm is worth keeping: **short sprints, a visible backlog, and a regular demo/review point.** This also maps naturally onto the 5 phases already defined in the architecture doc — each phase becomes a mini-release, broken into 1–2 sprints.

- **Sprint length:** 2 weeks
- **Sprint ceremonies (trim to what your team size needs):**
  - **Sprint planning** (start of sprint, ~1 hr): pull items from backlog into the sprint
  - **Daily standup** (async is fine for small/remote teams — a Slack/Discord post: what I did, what I'm doing, blockers)
  - **Sprint review/demo** (end of sprint, ~30 min): show working software against real data, not slides
  - **Retro** (end of sprint, ~20 min): what worked, what didn't, one thing to change next sprint

If it's just you or a 2–3 person team, keep the ceremonies but make them lightweight — planning and review can be the same 30-minute session.

---

## 2. Team Roles

Even a small team should have these roles explicitly assigned — one person can wear multiple hats, but each responsibility needs an owner:

| Role | Responsibility | Notes |
|---|---|---|
| **Product Owner** | Owns the backlog, decides what "done" means for a feature, prioritizes | Should be whoever best understands the disaster-response use case |
| **Backend/Data Engineer** | Ingestion workers, API, database, PostGIS queries | Owns data correctness — this is the highest-risk area (bad hazard data = real-world harm) |
| **Frontend Engineer** | Web dashboard (React + MapLibre) | |
| **Mobile Engineer** | React Native app, push notifications | Can be the same person as Frontend if stack is shared |
| **GIS/Domain Specialist** | Validates hazard data accuracy, sources fault/volcano reference data, sanity-checks map output | Critical and often skipped — a dev team without domain input will ship confidently wrong hazard maps |
| **Data Scientist / ML Engineer** | Owns the Regional Seismic Risk Profiling module: dataset cleaning (Kaggle PHIVOLCS + USGS historical data), feature engineering, K-Means clustering, Random Forest training/tuning, model evaluation and versioning | Can be the same person as Backend/Data Engineer on a small team, but timebox it separately — model work has a very different rhythm (experiment → evaluate → retrain) than shipping API endpoints |
| **QA/Test owner** | Rotates through the team; owns test coverage for ingestion pipeline especially | |

> If this is a solo or 2-person capstone/personal project: still write these down as **hats you switch between**, and timebox each — it prevents "backend forever, frontend never" drift.

---

## 3. Backlog Structure (mapped to architecture phases)

Use the 5 phases from the architecture doc as **Epics**. Each epic breaks into sprint-sized stories.

```
EPIC 1: MVP — Earthquake feed ingestion + basic map
  ├─ Story: USGS GeoJSON ingestion worker
  ├─ Story: PostGIS schema + migration setup
  ├─ Story: REST endpoint GET /events
  ├─ Story: Web map showing last 7 days, PH bounding box
  └─ Story: Deploy MVP to staging VPS

EPIC 2: Real-time + PHIVOLCS local data
  ├─ Story: PHIVOLCS bulletin scraper (earthquake)
  ├─ Story: PHIVOLCS volcano bulletin scraper
  ├─ Story: WebSocket push channel
  └─ Story: Dedup logic (USGS event == PHIVOLCS event)

EPIC 3: Static hazard layers
  ├─ Story: Import GEM active fault shapefile → fault_lines table
  ├─ Story: Digitize/import PHIVOLCS fault atlas data (manual GIS work)
  ├─ Story: Volcano hazard zone overlays
  └─ Story: Map layer toggle UI

EPIC 4: Mobile app
  ├─ Story: React Native shell + navigation
  ├─ Story: FCM push notification integration
  ├─ Story: "Saved location" + proximity alert logic
  └─ Story: Offline cache of last-known hazard data

EPIC 5: Regional Seismic Risk Profiling (K-Means + Random Forest)
  ├─ Story: Acquire + clean Kaggle "Philippine Earthquakes from PHIVOLCS" dataset
  ├─ Story: Acquire + clean Kaggle "Philippine Earthquakes 1900–2025 from USGS" dataset
  ├─ Story: Merge/reconcile both historical sources, resolve schema differences
  ├─ Story: Feature engineering — aggregate per region (event count, mean/max magnitude,
  │         mean depth, spatial density)
  ├─ Story: K-Means clustering — determine k via elbow/silhouette, assign risk clusters
  ├─ Story: Random Forest classifier — train on cluster labels, evaluate (accuracy,
  │         precision/recall, feature importances)
  ├─ Story: Persist model artifacts (joblib) + write region_risk_profiles to PostGIS
  ├─ Story: REST endpoints GET /risk-profile/:region, GET /risk-profile/clusters
  └─ Story: Web dashboard risk-profile map layer + region lookup

EPIC 6: Stretch — landslide + InSAR
  ├─ Story: Landslide susceptibility static layer import
  └─ Story: Sentinel-1 InSAR data pipeline (research spike first)
```

**Story sizing tip:** if a story can't be demoed at the end of a sprint, it's too big — split it.

---

## 4. Definition of Ready / Definition of Done

**Definition of Ready** (before a story enters a sprint):
- Data source/API confirmed reachable and documented
- Acceptance criteria written (what does "working" look like)
- No unresolved dependency on another in-progress story

**Definition of Done** (before a story is closed):
- Code merged via PR with at least one review (self-review is fine solo, but do it deliberately — reread your own diff before merging)
- For data-pipeline stories: tested against **real** API responses, not just mocked data
- For map/frontend stories: checked on both desktop and mobile viewport
- For ML stories (clustering/classification): evaluated against a held-out split of the historical dataset, metrics recorded (silhouette score for K-Means; accuracy/precision/recall/confusion matrix for Random Forest), and the resulting model artifact + metadata (dataset snapshot version, training date) committed/stored, not just "trained once in a notebook and forgotten"
- Deployed to staging and demoed

---

## 5. Git & Branching Workflow

Simple trunk-based flow — avoids the overhead of GitFlow for a project this size:

- `main` — always deployable
- `feature/<short-name>` branches off `main`, PR back into `main`
- Squash-merge PRs to keep history clean
- Tag releases at the end of each Epic (`v0.1-mvp`, `v0.2-realtime`, etc.)

**Commit convention (Conventional Commits):**
```
feat: add USGS ingestion worker
fix: dedup logic missing PHIVOLCS source check
docs: update architecture doc with InSAR notes
```

---

## 6. Tooling

| Purpose | Tool | Why |
|---|---|---|
| Backlog/board | GitHub Projects (if already using GitHub) or Trello/Linear | Free, low overhead — don't reach for Jira unless the team is big |
| CI/CD | GitHub Actions | Matches the deployment approach in the architecture doc |
| Error tracking | Sentry | Free tier is enough at this scale |
| Async standups | Slack/Discord channel, one thread per day | No meeting needed |
| Docs | This repo's `/docs` folder in Markdown | Keep architecture + framework docs versioned with the code |
| ML / data science | `scikit-learn` (KMeans, RandomForestClassifier), `pandas`/`geopandas`, Jupyter notebooks, `joblib` for model persistence | Standard, well-documented stack; no need for heavier MLOps tooling (MLflow, etc.) at this project's scale unless retraining frequency grows |
| Dataset acquisition | Kaggle API / manual export | Historical training data for the risk-profiling module (see architecture doc §4) — pulled once per retraining cycle, not polled |

---

## 7. Testing Strategy (by layer)

| Layer | What to test | How |
|---|---|---|
| Ingestion workers | Correct parsing of USGS/PHIVOLCS payloads, dedup logic, handling of malformed/missing data | Unit tests with saved real API response fixtures |
| API | Endpoint contracts, spatial query correctness (e.g., "events within radius") | Integration tests against a test PostGIS instance |
| ML — feature engineering | Per-region aggregation (event count, mean/max magnitude, mean depth, density) matches hand-computed values on a small fixture slice of the Kaggle datasets | Unit tests against a saved, trimmed-down CSV fixture (not the full dataset) |
| ML — clustering | Silhouette score above an agreed threshold; cluster count `k` is chosen deliberately, not hardcoded without justification | Run as part of the training script; log metrics each run |
| ML — classification | Random Forest accuracy/precision/recall on a held-out test split; feature importances reviewed for plausibility (e.g., magnitude/frequency should outrank incidental features) | Evaluation script run each retraining cycle, results committed to `docs/` or a metrics log |
| Web/mobile | Map renders correct markers for known fixture data | Component tests + manual QA against staging |
| End-to-end | A real event flows from ingestion → DB → API → shows on map within expected latency | Run manually each sprint review; automate once the pipeline stabilizes |

**Special note for the ML module:** because K-Means cluster numbering can shift between retraining runs, pin cluster→label mapping deliberately (e.g., order clusters by ascending mean magnitude before assigning Low/Moderate/High/Very High) and treat a silent mismatch here as a **P0** bug — it would mislabel a region's risk level without any obvious error.

**Special note for this project:** because this is disaster-risk data, treat data-correctness bugs as **P0** regardless of how small they look — a wrong coordinate or a missed dedup can misrepresent real hazard risk to actual people.

---

## 8. Suggested Sprint Timeline

| Sprint | Focus | Maps to |
|---|---|---|
| 1–2 | MVP: ingestion + basic map | Epic 1 |
| 3–4 | Real-time + PHIVOLCS scraping | Epic 2 |
| 5–6 | Static hazard layers (faults, volcano zones) | Epic 3 |
| 7–9 | Mobile app + push notifications | Epic 4 |
| 10–12 | Regional Seismic Risk Profiling: dataset prep, K-Means clustering, Random Forest classifier, risk-profile map layer | Epic 5 |
| 13+ | Stretch: landslide, InSAR | Epic 6 |

~5 months to a solid v1 (Epics 1–4) at 2-person part-time pace, plus roughly another 4–6 weeks for the risk-profiling module (Epic 5) given dataset prep and model iteration time; faster with a dedicated team or a team member focused solely on the ML track in parallel with Epics 3–4.