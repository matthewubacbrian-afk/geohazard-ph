# Task 06 — Risk and volcano panels

## Goal
Restyle risk profile and volcano bulletin panels, and make the existing region lookup reachable in the active risk panel.

## Acceptance
- Keep `useRiskProfiles` and `useVolcanoes` as the only data hooks; region filtering uses the already-loaded profile array.
- Do not call `fetchRiskProfile` or change API requests, types, or mapping.
- Search input is labeled `Filter regions`; its local query filters both lookup rows and profile cards, and clearing it restores all loaded profiles.
- Preserve values, feature drivers, model/dataset metadata, loading/error/retry/empty states, volcano links, observation/retrieval timestamps, stale cache text, and the distinction between alert level `0` and `null`.
- Keep risk labels textual and pair risk palette cues with non-color shapes/patterns.
- Show the required sentence: “Risk profiles are descriptive statistics, not earthquake predictions.”
- Update SDD report, run focused tests and web build, and commit as `feat: expose region lookup in risk panel`.

## Protected scope
Presentation components/styles and their tests only. No backend, API client, hooks, or types changes. Do not start app services; final app verification belongs to Task 7.
