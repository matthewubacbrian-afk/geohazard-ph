# GeoHazard Starter Scaffold Design

## Goal

Create the GeoHazard PH monorepo file tree as a runnable starter scaffold based on the provided project overview, architecture, development framework, and file-tree reference documents.

## Approach

The scaffold follows the recommended full starter layout: FastAPI backend and ingestion workers, React/Vite web dashboard, React Native mobile shell, Docker Compose services for PostGIS and Redis, infra placeholders, static data folders, scripts, and versioned docs.

## Boundaries

This setup creates starter files and clear extension points. It does not implement production ingestion, real PHIVOLCS scraping, live push notifications, GIS tile generation, mobile native projects, or deployment credentials.

## Verification

A repository verifier at `scripts/verify_structure.py` checks that the expected scaffold paths exist. Backend and web test files are included as starter targets for the first implementation phase.
