# Task 2 Brief — Shared navigation and information pages

## Objective
Restyle shared navigation, settings, and informational routes under the approved web redesign while preserving route behavior, source attribution, honest unavailability, and settings callbacks.

## Constraints
- UI-only; no API, hook, type, backend, ML, or mobile changes.
- Use CSS Modules and semantic design tokens; no icon fonts or palette literals in component CSS.
- Preserve the separate uncommitted dashboard scroll files/test.
- Add keyboard accessibility assertions before implementation, demonstrate red, then implement.

## Acceptance
- Navigation retains route targets and current-page meaning with keyboard-operable controls.
- Settings receives focus on open, traps Tab/Shift+Tab, closes on Escape, and preserves existing close actions.
- Hero describes available public data and methods without prediction claims or invented sample meters.
- About includes exact risk and non-official-advisory messaging; Data Sources and Historical retain their factual/source and unavailable content.
- Focused tests and production build pass; inspect intended page widths if the app service is available without violating the stopped-services instruction.
