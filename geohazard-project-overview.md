# GeoHazard PH — Project Overview

**Full title:** GeoHazard PH — Regional Seismic Risk Profiling in the Philippines Using
K-Means Clustering and Random Forest Classification

*Companion to `geohazard-system-architecture.md` and `geohazard-development-framework.md`*

---

## 1. Introduction / Background

The Philippines sits along the Pacific Ring of Fire and is crossed by multiple active fault systems (e.g., the West Valley Fault), making it highly exposed to earthquakes, volcanic eruptions, and secondary hazards like landslides and ground movement. Existing efforts such as DOST's **Project NOAH** demonstrated the value of a centralized, public-facing hazard information platform — but NOAH's original focus was primarily hydrometeorological (flood, rainfall, storm surge).

**GeoHazard PH** proposes a complementary system focused on **geologic and seismic hazards** — earthquakes, volcanic activity, active faults, and ground movement — built entirely on public, freely accessible data sources (USGS, PHIVOLCS, Smithsonian GVP), without requiring a private sensor network.

---

## 2. Objectives

**General Objective:**
To design and develop a web and mobile-based multi-hazard monitoring system that aggregates public earthquake, volcanic, and geologic hazard data into a single, accessible platform for public awareness and disaster preparedness.

**Specific Objectives:**
1. To collect and normalize real-time earthquake data from public APIs (USGS) and local sources (PHIVOLCS).
2. To display volcanic activity status and alert levels for Philippine volcanoes using public data (Smithsonian GVP, PHIVOLCS).
3. To provide a reference layer of active fault lines so users can understand their proximity to known seismic hazards.
4. To deliver real-time push notifications to mobile users based on proximity to newly detected hazard events.
5. To present all of the above through an interactive, map-based web dashboard and companion mobile app.
6. To profile Philippine regions/provinces into distinct seismic risk groups using **K-Means clustering** on historical earthquake characteristics (frequency, magnitude, depth, spatial density).
7. To train a **Random Forest classifier** that assigns a risk-level label (e.g., Low/Moderate/High/Very High) to a region, using the K-Means-derived clusters as ground-truth labels, so that risk classification can be produced for regions or time windows beyond the original clustering run.

---

## 3. System Functionality

### 3.1 Core Features

| Feature | Description |
|---|---|
| **Real-time Earthquake Monitoring** | Displays recent earthquakes (magnitude, depth, location, time) sourced from USGS and PHIVOLCS, plotted on an interactive map |
| **Volcanic Activity Tracker** | Shows current alert levels for monitored Philippine volcanoes (e.g., Mayon, Taal, Pinatubo), with historical eruption context |
| **Active Fault Reference Map** | Overlay of known active fault lines (from PHIVOLCS Fault Atlas and the GEM Global Active Faults Database) so users can see fault proximity to their location |
| **Ground Movement / Deformation Layer** *(stretch goal)* | Satellite-derived (InSAR) ground deformation data to flag areas of unusual movement, relevant to both seismic and landslide risk |
| **Landslide Susceptibility Overlay** *(stretch goal)* | Static susceptibility layer sourced from NASA/PHIVOLCS/MGB datasets |
| **Location-based Alerts** | Mobile push notifications when a hazard event occurs within a user-defined radius of their saved location(s) |
| **Historical Event Browser** | Filterable list/timeline of past events by hazard type, date range, and magnitude/severity |
| **Map Layer Controls** | Toggle individual hazard layers on/off; filter by hazard type, time range, and severity |
| **Regional Seismic Risk Profiling** *(new — core analytical feature)* | Clusters provinces/regions into seismic risk groups via **K-Means** (based on historical event frequency, average/max magnitude, depth distribution, and spatial density of epicenters), then uses a **Random Forest classifier** trained on those cluster labels to assign a risk category to a region and to explain which features (frequency, magnitude, depth, proximity to faults) drive that classification |

### 3.2 Regional Seismic Risk Profiling (ML Component)

This is the analytical core that distinguishes GeoHazard PH from a pure monitoring dashboard:

- **Unsupervised stage — K-Means Clustering:** historical earthquake records are aggregated per region (province/administrative boundary or a fixed spatial grid over the Philippines) into features such as event count, mean/max magnitude, mean depth, and spatial density. K-Means groups regions into a set of seismic risk clusters (e.g., 3–5 clusters tuned via the elbow method / silhouette score).
- **Supervised stage — Random Forest Classification:** the cluster assignments from K-Means become the training labels for a Random Forest classifier. This lets the system classify a region's risk level directly from its feature vector without re-running clustering each time, and it exposes feature-importance rankings (e.g., "magnitude frequency" contributes more than "depth" to a High-risk classification) that are useful for the report/thesis discussion.
- **Output:** a per-region "risk profile" (cluster label + classifier-predicted label + confidence + contributing features) surfaced as a dedicated map layer and a searchable region lookup, alongside the real-time hazard-event layers.
- **Important framing:** this is a **statistical risk profiling tool based on historical patterns**, not an earthquake prediction system — it does not forecast when or where the next earthquake will occur. It should be described and presented as such throughout the platform and documentation, consistent with the "information and awareness tool" framing in §6.

### 3.3 User-Facing Functionalities

- **Web Dashboard:** full interactive map, layer controls, event history, designed for desktop use (LGU disaster offices, researchers, general public on desktop)
- **Mobile App:** lightweight version focused on alerts, nearby hazards, and quick-glance status — designed for on-the-go use during actual events, including offline caching of the last-known data in case of connectivity loss

### 3.4 Administrative/Backend Functionalities

- Scheduled ingestion of data from all public sources, with deduplication (e.g., the same earthquake reported by both USGS and PHIVOLCS should appear once)
- Data validation and error logging for ingestion failures (source downtime, malformed data)
- Periodic refresh of static reference layers (fault lines, susceptibility maps) on a slower cadence than live event data
- Scheduled/manual retraining of the K-Means + Random Forest models as new historical data or updated Kaggle dataset snapshots become available

---

## 4. Target Users

| User group | Use case |
|---|---|
| **General public** | Awareness of nearby hazards, real-time alerts, disaster preparedness |
| **Local Government Units (LGUs) / disaster response offices** | Situational awareness for response coordination |
| **Students / researchers** | Access to historical hazard data for study |
| **Schools / community organizations** | Reference tool for disaster-preparedness education |

---

## 5. Scope

The system covers:
- Earthquake events (Philippine region, sourced from USGS + PHIVOLCS)
- Volcanic activity status (Philippine volcanoes, sourced from GVP + PHIVOLCS)
- Active fault line reference data (static layer)
- Location-based push notifications for mobile users
- Regional seismic risk profiling (K-Means clustering + Random Forest classification), trained on historical earthquake datasets:
  - [Philippine Earthquakes from PHIVOLCS (Kaggle)](https://www.kaggle.com/datasets/bwandowando/philippine-earthquakes-from-phivolcs)
  - [Philippine Earthquakes 1900–2025 from USGS (Kaggle)](https://www.kaggle.com/datasets/bwandowando/philippine-earthquakes-1900-2025-from-usgs)

These curated Kaggle datasets are used specifically as the **historical training corpus** for the clustering/classification models — this is distinct from the live USGS/PHIVOLCS ingestion described above, which feeds the real-time map layers. Using pre-compiled datasets here avoids re-scraping decades of PHIVOLCS bulletins just to build a training set.

## 6. Limitations

- **No private sensor network** — the system depends entirely on the accuracy, availability, and update frequency of public data sources; it cannot detect events faster or more precisely than those sources do.
- **PHIVOLCS has no official public API** — local-intensity data (PEIS scale) and volcano bulletins are obtained via web scraping, which is inherently fragile to source website changes.
- **Fault line and susceptibility data are static reference layers**, not real-time — they reflect the last available survey/study, not live ground conditions.
- **InSAR ground-deformation and landslide-susceptibility features are stretch goals**, not part of the core v1 system, due to the specialized processing they require.
- **The K-Means clusters and Random Forest risk labels are descriptive/statistical, not predictive of specific future events** — they summarize historical seismicity patterns per region and should never be presented as a forecast of when or where an earthquake will strike.
- **Model quality depends on the completeness and recency of the underlying Kaggle historical datasets** — both are static snapshots (PHIVOLCS-sourced and USGS 1900–2025), so the risk profile should be periodically retrained/refreshed rather than treated as permanently accurate, and any gaps or reporting biases in the original PHIVOLCS/USGS records carry through into the clustering results.
- The system is an **information and awareness tool**, not an official early-warning authority — it is not a replacement for official PHIVOLCS/NDRRMC advisories, and should direct users to those for authoritative action guidance during actual emergencies.

---

## 7. Significance

- **To the public:** provides a single, accessible place to check multiple geologic hazard types at once, rather than checking PHIVOLCS, USGS, and GVP separately.
- **To disaster preparedness:** proximity-based alerts and fault-line awareness can help individuals and communities understand their specific risk exposure, not just national-level news.
- **To research/education:** a historical, queryable event database lowers the barrier for students and researchers studying Philippine seismic activity.
- **To future development:** the architecture is designed to extend toward hydrometeorological hazards (flood, storm surge) later, potentially converging back toward a NOAH-like unified multi-hazard platform.