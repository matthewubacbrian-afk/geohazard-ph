# Mobile fast-xml-parser consumer-call review — 2026-10-20

This review narrows one of the six direct advisory references in the
[mobile path record](mobile-advisory-exposure-review-2026-10-20.md):
[GHSA-gh4j-gqv2-49f6](https://github.com/advisories/GHSA-gh4j-gqv2-49f6) for
`fast-xml-parser` 4.5.7. That advisory describes `XMLBuilder` comment and CDATA
delimiter output. It does not say that every `XMLParser` call exercises the
affected operation. The project has 34 npm production-graph findings; this
review changes **none** of their `undetermined` dispositions.

## Reproducible source scope

The tracked `mobile/package-lock.json` resolves both
`@react-native-community/cli-platform-android` and
`@react-native-community/cli-platform-apple` to 14.1.0, and
`fast-xml-parser` to 4.5.7. The iOS path reaches the Apple package through
`@react-native-community/cli-platform-ios` 14.1.0. The two 14.1.0 npm tarballs
were downloaded with `npm pack` outside the repository; their SHA-512 digests
matched the lockfile `integrity` values. Searching every published `build/*.js`
file in those two tarballs for `fast-xml-parser`, `XMLParser`, `XMLValidator`, and
`XMLBuilder` found the three direct import/use files below and no direct
`XMLBuilder` call. Exact-version upstream source is linked for review.

| Published consumer and source | Operation found | Input origin visible in that function | Advisory-operation observation |
| --- | --- | --- | --- |
| Android CLI `getMainActivity` ([v14.1.0 source](https://github.com/react-native-community/cli/blob/v14.1.0/packages/cli-platform-android/src/config/getMainActivity.ts)) | `XMLValidator.validate` followed by `XMLParser.parse` | Reads the local `AndroidManifest.xml` at the supplied `manifestPath` | No direct `XMLBuilder` call in the published Android CLI package. |
| Apple CLI `getInfo` ([v14.1.0 source](https://github.com/react-native-community/cli/blob/v14.1.0/packages/cli-platform-apple/src/tools/getInfo.ts)) | `XMLParser.parse` on a workspace branch; a non-workspace branch uses `xcodebuild -list -json` | Reads local `contents.xcworkspacedata` from the selected Xcode workspace | No direct `XMLBuilder` call in the published Apple CLI package. |
| Apple CLI `getBuildConfigurationFromXcScheme` ([v14.1.0 source](https://github.com/react-native-community/cli/blob/v14.1.0/packages/cli-platform-apple/src/tools/getBuildConfigurationFromXcScheme.ts)) | `XMLParser.parse` | Reads a local `.xcscheme` file under the selected `.xcodeproj` | No direct `XMLBuilder` call in the published Apple CLI package. |

These functions run in the Node.js CLI tooling path and read local project
files. This source review does not prove who can control those files in every
build environment, whether another transitive consumer invokes `XMLBuilder`,
or whether affected code is packaged into a device executable. The Android
and iOS Release source maps list only `react-native` among the 34 audit
finding names; that package-name observation is not an execution trace.
The direct `fast-xml-parser` finding and inherited findings therefore stay
**undetermined**. A later attack-path review must cover other consumers and
build inputs, then repeat the analysis after the framework migration.
