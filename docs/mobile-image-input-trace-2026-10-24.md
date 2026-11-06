# Mobile Release image-input trace — 2026-10-24

This bounded review observes the pinned `image-size` parser during the Android
and iOS non-published Release commands in [PR #66](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/66).
The first [exact-head CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40102838837)
used `140d2d60`; backend, ML, web, Android, and iOS checks passed on that head.
Its artifacts include `mobile-image-input-trace-android`,
`mobile-image-input-trace-ios`, `mobile-artifact-report-android`,
`mobile-artifact-report-ios`, and both `mobile-process-trace-*` summaries.
This is build-process evidence, not a device or vulnerability disposition.

## Observed build activity

The preload observer ran only inside the existing Release commands. Its compact
summarizer required an executed Metro `Server.build`, a matching V8 coverage file
and observer activation for every covered Node process/thread, and agreement
between `imageSize` function-entry counts and recorded parser calls. The raw
JSONL, V8 coverage, source maps, and app binaries stayed out of Git and out of
the uploaded trace artifacts. Call records would contain coarse input classes,
counts, and digests, not raw bytes or absolute paths.

| Compact Release trace field | Android | iOS |
| --- | ---: | ---: |
| Covered and activated Node process/thread pairs | 12 | 10 |
| Threads that executed Metro `Server.build` | 1 | 1 |
| Pinned `image-size` module loads | 2 | 2 |
| Observed parser calls and V8 parser entries | 0 | 0 |

The two module loads per platform do not imply that an image was parsed. A
separate local Android Metro bundle with the same observer had one covered build
thread, one module load, and zero parser calls. That local probe is not an
Android Release or iOS result. The independent review reproduced a resolved-path
`require` bypass, then verified its regression fix, worker-thread correlation,
and the pinned parser's V8 invocation count against observed calls.

## Release-report comparison and live audit change

The previous audited [PR #65](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/65)
reports contained 34 production dependency-chain rows: 28 high and six
moderate, with six direct advisory references across five installed packages.
The PR #66 live audit returned 12 rows on each platform: six high and six
moderate, with four direct references across `fast-xml-parser`, `image-size`,
and `node-forge`. Every current row remains `undetermined`. The 22 rows no
longer returned include `braces` and `sprintf-js` and packages with inherited
findings through those chains. The mobile lockfile was unchanged.
Four retained React Native CLI rows fell from high to moderate when their
inherited `braces` chain disappeared; two other retained high rows lost
withdrawn-advisory paths without changing severity. No new row appeared.

GitHub marked the [`sprintf-js` advisory](https://github.com/advisories/GHSA-hp3w-g68c-fv3c)
withdrawn on 2026-10-22 and the
[`braces` advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
withdrawn on 2026-10-23. These upstream withdrawals explain the changed live
audit inventory; they do not remove installed code or prove that a project
process or device is safe. The earlier 34-row reports remain accurate dated
snapshots, not the current advisory count.

Both PR #66 Release reports retain the PR #65 source-map hashes and 25-package
lists, the same selected native inventories, and unchanged JSON field sets.
The existing five-package process summaries match PR #65 exactly. Android's
APK file hash differs as expected for a rebuilt artifact; the iOS app bundle
hash matches. The only other report difference is the advisory list described
above. The final [exact-head CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40104717873) on `a80ecd85` passed all five checks. Its Android and iOS reports retained the same 12 undetermined rows and matched the first PR #66 run in every field except the Android APK hash. PR #66 merged at `c398d31c`.

## Limits and next gate

Zero parser calls describe only Node processes inheriting the scoped Release
environment. They do not cover install, Pod, or Debug steps, a future generated
or externally supplied asset, or actual Android/iOS device execution. A path
record, if one occurs later, is a snapshot immediately before the parser's own
read rather than an atomic view of its input. The two `image-size` advisory
preconditions remain unresolved for other build inputs; the current four direct
references and all 12 live findings retain `undetermined` dispositions.

The next active advisory slice should check remaining `fast-xml-parser`
`XMLBuilder` consumers and comment/CDATA input provenance, followed by
`node-forge` certificate/key provenance if an executing caller is found. The
withdrawn `braces` and `sprintf-js` references remain in historical reviews
but are no longer active audit gates unless reinstated or new evidence changes
their status. New Architecture readiness, a supported framework migration,
physical-device flows, staging, and Epic 5's held profile export remain
separate acceptance gates.
