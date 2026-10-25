# Mobile XML builder direct-consumer path — 2026-10-25

This review extends the [pinned CLI consumer review](mobile-fast-xml-parser-callsites-2026-10-20.md) from two CLI packages to the installed mobile JavaScript tree. It checks whether a direct consumer of `fast-xml-parser` 4.5.7 constructs or calls `XMLBuilder`, the affected operation in [GHSA-gh4j-gqv2-49f6](https://github.com/advisories/GHSA-gh4j-gqv2-49f6). It is a bounded source and build-process finding, not a vulnerability clearance or device execution claim. The current Android and iOS audits each contain 12 rows, all `undetermined`.

## Source scope and direct consumers

The tracked `mobile/package-lock.json` pins `fast-xml-parser` 4.5.7 and both `@react-native-community/cli-platform-android` and `@react-native-community/cli-platform-apple` 14.1.0. The local ignored installation inspected for this review reports the same three installed versions; it was preserved from the earlier PR #66 verification, not freshly installed for this source search. The later [PR #67 clean CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40167740282) supplies separate exact-Release execution evidence.

A text search covered 7,540 installed `.js`, `.cjs`, and `.mjs` files for `fast-xml-parser` or `XMLBuilder`, with ignored files included. The only matches were three direct CLI imports and the package's own `src/fxp.js` export. A search of tracked `mobile/src`, Android, iOS, and Metro configuration source returned no direct match. This is a direct-token inventory, not a proof that computed imports, generated code, or a future dependency cannot call the builder.

| Direct installed consumer | Input and operation in the published JavaScript | Builder finding |
| --- | --- | --- |
| Android CLI `build/config/getMainActivity.js` | Reads a local `AndroidManifest.xml`; invokes `XMLValidator.validate` and `XMLParser.parse`. | No direct `XMLBuilder` construction or `.build` call in this file. |
| Apple CLI `build/tools/getInfo.js` | Reads local `contents.xcworkspacedata` for workspace projects and invokes `XMLParser.parse`; its non-workspace branch reads `xcodebuild -list -json`. | No direct `XMLBuilder` construction or `.build` call in this file. |
| Apple CLI `build/tools/getBuildConfigurationFromXcScheme.js` | Reads a local `.xcscheme` and invokes `XMLParser.parse`. | No direct `XMLBuilder` construction or `.build` call in this file. |

The package's `src/fxp.js` exposes `XMLBuilder` internally; that match is not an external consumer. The earlier [exact-version tarball review](mobile-fast-xml-parser-callsites-2026-10-20.md) recorded lockfile-integrity matches and upstream source links for the three CLI files. The broader local installed-tree scan found no additional direct JavaScript import or builder token outside the package, but it does not replace an integrity check for every installed file.

## Exact-Release process observation

The [PR #67 Android and iOS Release process summaries](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40167740282) match PR #66's compact summaries. The Metro build sentinel executed on both platforms. Android had 12 V8 coverage files and iOS had 10. On each platform, 12 `fast-xml-parser` files loaded and 41 distinct named function positions executed. The loaded set included `src/xmlbuilder/json2xml.js` and `src/xmlbuilder/orderedJs2Xml.js`; neither file had a recorded executed named function. Parser and validator functions did execute. A loaded builder file is therefore not evidence that the affected builder operation ran in these scoped commands.

The final Android/iOS Release reports both retain the same 12 `undetermined` rows, 25 source-map packages, source-map hashes, native inventories, and five-package process summaries as PR #66. The image-input traces also match; only the Android APK file hash differs. These reports do not attribute the package to code executing on a physical device.

## Advisory gate and limits

The active advisory concerns `XMLBuilder` emitting unescaped comment `-->` or CDATA `]]>` delimiters from supplied values. A reachable project path would require a builder call, attacker-controlled values reaching those comment/CDATA fields, and a consequential XML consumer. This review found no direct builder consumer in the inspected installed JavaScript and no executed named builder function in the scoped Release commands. It did not establish the full chain or rule it out in other builds, dynamic/generated callers, anonymous functions, external inputs, or physical-device processes. It makes no build-only or safety classification. The direct `fast-xml-parser` row and every inherited current audit row remain `undetermined`.

The next advisory evidence slice is `node-forge`/`selfsigned` caller and certificate/key provenance. Recheck package versions, audit identities, process activity, and artifact contents after the framework migration; preserve the separate [Epic 5 hold and device/staging gates](../PLAN.md).
