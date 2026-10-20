# Mobile advisory path and precondition review — 2026-10-20

This is a bounded review of the current React Native 0.75.5 lockfile and the
non-published Android/iOS Release reports from
[PR #55](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/55). Its
[five-check run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/39381136781)
reported 34 npm production-graph findings on each platform: six moderate, 28
high, and zero critical. Five directly affected packages account for six direct
advisory references; another 29 finding rows inherit an affected dependency.
Both reports provide exact installed lockfile versions. Every finding remains
**undetermined**. The seven-day CI attachments will expire; the essential
observations are preserved here and in the
[artifact evidence](mobile-artifact-evidence-2026-10-20.md).

## How the dependency paths were checked

From `mobile/` at merged commit `bed6c572`, run:

```powershell
npm ls braces fast-xml-parser image-size node-forge sprintf-js --omit=dev --package-lock-only --all --json
```

This reads the tracked lockfile without installing packages. The following are
the shortest root-to-affected-package paths displayed by that production-graph
tree. `react-native` is the direct root package. The tree also displayed an
additional `fast-xml-parser` path through
`react-native > @react-native-community/cli-platform-ios > @react-native-community/cli-platform-apple > fast-xml-parser`.

| Installed package | Shortest observed production-graph path |
| --- | --- |
| `braces` 3.0.3 | `react-native > @react-native-community/cli-platform-android > fast-glob > micromatch > braces` |
| `fast-xml-parser` 4.5.7 | `react-native > @react-native-community/cli-platform-android > fast-xml-parser` |
| `image-size` 1.2.1 | `react-native > @react-native/community-cli-plugin > metro > image-size` |
| `node-forge` 1.4.0 | `react-native > @react-native/community-cli-plugin > @react-native/dev-middleware > selfsigned > node-forge` |
| `sprintf-js` 1.0.3 | `react-native > @react-native/community-cli-plugin > metro-config > cosmiconfig > js-yaml > argparse > sprintf-js` |

These are lockfile dependency paths, **not** observed execution traces or
packaged-code paths. The app's `mobile/src` has no direct import of these five
packages. None of their package names was listed in either Release JavaScript
source map; `react-native` was the sole audit finding name listed (404 Android
and 400 iOS source entries). The Android inventory lists 196 selected `.so`
entries, and the iOS inventory lists the app and Hermes executables. Those
observations do not attribute statically linked native code, Android DEX, or
build-time effects to an advisory package.

## Advisory-specific operation required

The installed versions are within the affected ranges reported by npm and the
linked GitHub Advisory Database records. The operation column describes the
advisory's trigger; it does **not** assert that this project calls the affected
operation with attacker-controlled input.

| Advisory and installed package | Affected operation and input precondition | Current project evidence |
| --- | --- | --- |
| [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm), `braces` 3.0.3 (`<=3.0.3`) | Recursive brace-pattern parsing or expansion of a sufficiently deep pattern can exhaust the Node.js call stack. | Reached through CLI glob matching in the lockfile; pattern origin and whether an untrusted pattern reaches `braces` remain unverified. |
| [GHSA-gh4j-gqv2-49f6](https://github.com/advisories/GHSA-gh4j-gqv2-49f6), `fast-xml-parser` 4.5.7 (`<5.7.0`) | `XMLBuilder` emits unescaped comment or CDATA delimiters if those values contain attacker-controlled `-->` or `]]>`. | The [bounded consumer-call review](mobile-fast-xml-parser-callsites-2026-10-20.md) found three direct `XMLParser`/`XMLValidator` uses and no direct `XMLBuilder` call in the pinned Android and Apple CLI packages. Other consumers, input control, and reachability remain unverified. |
| [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq), `image-size` 1.2.1 (`>=1.2.0 <=2.0.2`) | Parsing a crafted JXL or HEIF buffer with a zero-sized box can loop indefinitely in a Node.js process. | The [bounded Metro consumer-call review](mobile-image-size-callsites-2026-10-20.md) found asset path/buffer calls and byte-signature format selection; attacker control of a crafted asset remains unverified. |
| [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr), `image-size` 1.2.1 (`>=0.6.3 <=2.0.2`) | Parsing a crafted ICNS buffer with a zero-length entry can loop indefinitely in a Node.js process. | The same Metro asset calls can dispatch by bytes despite an extension gate; a crafted ICNS input path and attacker control remain unverified. |
| [GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv), `node-forge` 1.4.0 (`<=1.4.0`) | RSA PKCS#1 v1.5 signature verification can accept extra nested `DigestAlgorithm` elements with low-exponent keys. | The [bounded consumer-call review](mobile-node-forge-callsites-2026-10-20.md) found no direct `selfsigned` use in the pinned middleware's published JavaScript. `selfsigned.generate` does verify the certificate it creates, but no path for a crafted external signature or low-exponent key was established. |
| [GHSA-hp3w-g68c-fv3c](https://github.com/advisories/GHSA-hp3w-g68c-fv3c), `sprintf-js` 1.0.3 (`<=1.1.3`) | A caller-supplied format string with an out-of-range precision can throw an uncaught `RangeError`. | The path is through Metro configuration/YAML argument parsing; the origin of any format string passed to `sprintf-js` has not been traced. |

The npm result counts package-chain findings, not six independently exploitable
paths. A package's presence in that graph or absence from a JavaScript source
map does not establish whether it is build-only, reachable in a distributed app,
or safe for an operator to ignore. The advisory pages describe vulnerabilities
in Node.js library operations; the current Release reports do not prove that
those operations run on an Android or iOS device.

## Evidence still needed

1. Inspect the pinned transitive consumers at their installed versions to find
   actual calls to the affected `braces`, `XMLBuilder`, image parsers,
   `node-forge` verification, and `sprintf-js` format APIs. Record the caller
   file/function and whether input is fixed, local, or user-controlled.
2. Trace any untrusted input from a reachable build or runtime entry point to
   that call, including whether the affected code is present in the distributed
   JS bundle, Android DEX/native code, or iOS executable. Record a negative
   conclusion only with enough evidence to support it.
3. Recheck the audit, exact versions, paths, and Release artifacts after the
   supported React Native migration. Device flows remain a separate Epic 4
   acceptance gate.

Until those checks are complete, all 34 finding dispositions stay
**undetermined**. This record is dependency and advisory triage, not a release
security signoff or a change to the held-profile, deployment, or source-data
decisions.

The [bounded `fast-xml-parser` consumer-call review](mobile-fast-xml-parser-callsites-2026-10-20.md)
inspects the pinned Android and Apple CLI packages. Their published code uses
`XMLParser` and `XMLValidator` on local project files and contains no direct
`XMLBuilder` call; other consumer paths and input control remain open.
The [bounded `image-size` consumer-call review](mobile-image-size-callsites-2026-10-20.md)
inspects Metro's asset path/buffer calls and byte-based format dispatch;
crafted-input provenance remains open for both parser-loop advisories.
The [bounded `node-forge` consumer-call review](mobile-node-forge-callsites-2026-10-20.md)
records the middleware manifest-only edge and `selfsigned.generate` certificate
verification; external signature input and an actual middleware call remain unverified.
