# Mobile Release build-process trace - 2026-10-21

This record examines Node V8 coverage from the non-published Android and iOS
Release builds in [PR #64](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/64),
at head `a4064e3372ac23a2d4627775056e6714dadec886`. It describes build
activity, not a vulnerability disposition or device execution. All 34 mobile
audit finding dispositions remain **undetermined**.

## Scope and verified artifacts

The [Mobile CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/39612915573)
passed its Android `mobile` and `ios-simulator` jobs. The separate backend,
ML, and web checks passed on the same head. `NODE_V8_COVERAGE` was set only
around the existing Gradle `assembleRelease` and iOS `xcodebuild` Release
commands.
The summarizer required a positive named `metro/src/Server.js` `build`
function entry before reporting package absences. It uploaded compact JSON
summaries, not the raw coverage files or app binaries. The Android summary
read 12 coverage files; iOS read 10. Their five package sections match.

| Directly affected installed package | Loaded files on each platform | Executed named functions on each platform | Bounded observation |
| --- | ---: | ---: | --- |
| `braces` 3.0.3 | 7 | 0 | Package files were loaded; no named function entry was recorded. The earlier CLI/cache pattern and input-provenance gate remains open. |
| `fast-xml-parser` 4.5.7 | 12 | 41 | Named XML parsing and validation functions ran, including `XMLParser.parse` and `exports.validate`. XML builder files loaded, but no named function from those files was recorded. The comment/CDATA output advisory's affected operation was not observed as a named call in these runs. |
| `image-size` 1.2.1 | 25 | 0 | The detector and format-handler files, including JXL, HEIF, and ICNS handlers, loaded. No named function entry was recorded; loading those handlers does not mean an affected parser ran. |
| `node-forge` 1.4.0 | 0 | 0 | No file under this direct package was recorded as loaded in the scoped Release commands. |
| `sprintf-js` 1.0.3 | 0 | 0 | No file under this direct package was recorded as loaded in the scoped Release commands. |

Both final Release reports were compared with the audited [PR #63](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/63)
baseline. Each still has 34 `undetermined` advisory rows and 25 source-map
packages, with identical source-map hashes and native inventories. All report
fields match their platform's baseline except the Android APK file hash; the
iOS app bundle hash also matches. The Release-report JSON format did not
change.

## Interpretation and next gate

V8 coverage records function entry in Node processes inheriting the Release
command's environment. It does not capture arguments, input control, device
execution, or every possible dynamic call; a file's top-level entry can show
module loading without use of its affected API. The trace excludes separate
install, Pod, and Debug steps, and a process that did not inherit this
environment. No absence here establishes build-only status, safety, or an
unreachable attack path.

The next bounded advisory slice should trace `image-size` call and input
provenance in Metro, including generated or externally supplied assets. The
exact Release build loaded its detector and advisory-relevant handler files,
while the previous [asset inventory](mobile-image-asset-provenance-2026-10-21.md)
found no current JXL, HEIF, or ICNS signatures. Whether an affected parser
receives crafted bytes remains unverified. The separate `braces` pattern,
`fast-xml-parser` builder, `node-forge` certificate, and `sprintf-js` format
gates in the [advisory matrix](mobile-advisory-attack-path-gates-2026-10-21.md)
also stay open. Repeat this build observation after dependency or framework
changes, and require device evidence before claiming runtime behavior.
