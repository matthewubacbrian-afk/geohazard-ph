# Geohazard Starter Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full starter monorepo scaffold for GeoHazard PH.

**Architecture:** Create a Python/FastAPI backend with ingestion boundaries, a React/Vite web app, a React Native mobile shell, Docker Compose local infrastructure, versioned docs, data folders, and setup scripts. Keep all files minimal so the next phase can add real ingestion and map behavior without restructuring.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy, pytest, React, TypeScript, Vite, React Native, Docker Compose, PostgreSQL/PostGIS, Redis.

---

### Task 1: Structure Verification

**Files:**
- Create: `scripts/verify_structure.py`

- [x] **Step 1: Write verifier for expected paths**
- [x] **Step 2: Run verifier before scaffold**
- [x] **Step 3: Confirm it fails because expected paths are missing**

### Task 2: Project Skeleton

**Files:**
- Create root files, `docs/`, `backend/`, `web/`, `mobile/`, `infra/`, `data/`, and `scripts/`

- [x] **Step 1: Add root metadata and Docker Compose**
- [x] **Step 2: Add versioned docs, ADR, runbook, and data-source notes**
- [x] **Step 3: Add backend package, app, ingestion, DB, fixtures, and tests**
- [x] **Step 4: Add web package, dashboard shell, components, hooks, API client, and tests**
- [x] **Step 5: Add mobile shell, services, screens, and tests**
- [x] **Step 6: Add infra placeholders and import scripts**

### Task 3: Verification

**Files:**
- Use: `scripts/verify_structure.py`

- [ ] **Step 1: Run scaffold verifier**

Run: `python scripts/verify_structure.py`

Expected: exit code 0 with all expected paths present.
