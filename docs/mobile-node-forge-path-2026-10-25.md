# Mobile node-forge direct-caller path — 2026-10-25

This review extends the [pinned `node-forge`/`selfsigned` source review](mobile-node-forge-callsites-2026-10-20.md) from the React Native development middleware tarball to the installed mobile JavaScript tree. It concerns the active [GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv) for crafted RSA PKCS#1 v1.5 signature verification in `node-forge` through 1.4.0. The result is a bounded direct-caller and exact-build finding, not a vulnerability clearance or device claim. All 12 rows in the current Android/iOS audit remain `undetermined`.

## Pinned source and caller inventory

`mobile/package-lock.json` resolves `react-native` 0.75.5 through `@react-native/dev-middleware` 0.75.5 to `selfsigned` 2.4.1 and `node-forge` 1.4.0. The preserved ignored local installation used for this source scan reports the same versions; it was not freshly installed for this review. The [PR #68 clean CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40170546617) supplies separate Release process evidence.

A direct-token search of 7,540 installed `.js`, `.cjs`, and `.mjs` files, including hidden files, for `selfsigned` or `node-forge` returned only `selfsigned/index.js` and `selfsigned/test/tests.js`. The latter is a package test, not a project call site. Tracked `mobile/src`, Android, iOS, and Metro configuration source had no matching token. No external direct JavaScript import or `selfsigned.generate` call was found in this installed-tree snapshot. The earlier tarball review separately confirmed that the pinned dev-middleware's 17 published JavaScript files have no direct import. These text searches do not exclude computed imports, generated code, other install trees, or future framework versions.

## Internal verification and input gate

The installed `selfsigned/index.js` requires `node-forge`. `generate` creates and signs a certificate, puts that same certificate into a CA store, and calls `forge.pki.verifyCertificateChain(caStore, [cert], callback)`. This is a real verification call if `generate` executes; calling the dependency only "certificate generation" would be inaccurate. The default path generates an RSA key pair, while the synchronous `options.keyPair` path parses caller-supplied PEM keys. No direct project caller or path supplying that option was found in the inspected installed JavaScript.

The advisory requires a crafted signature with extra nested `DigestAlgorithm` elements and a low-exponent key at an affected RSA verification path. A library API accepting caller-supplied keys does not establish that a project process receives such a signature or key. The certificate checked by this visible `selfsigned.generate` path is the certificate it just constructed; this source observation does not prove every possible caller or forge verification path is safe.

## Exact-Release observation and limits

The [PR #68 Android and iOS process summaries](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40170546617) each recorded an executed Metro build sentinel. Android had 12 V8 coverage files and iOS had 10. Neither summary recorded a loaded `node-forge` file or executed named forge function during its scoped non-published Release command. The final Release reports retained the same 12 `undetermined` rows, 25 source-map packages, source-map hashes, native inventories, and compact process/image traces as PR #67; only the Android APK file hash differed. The `node-forge` audit row remains `undetermined` on both platforms.

The V8 scope does not cover separate installation, Pods, Debug, dynamic/generated calls outside the observed process set, or physical-device execution. Package-name absence in source maps does not establish build-only status. A later disposition needs an actual entry point, certificate and key provenance, the crafted-signature preconditions, the executing process, and its error/timeout effect. Repeat the audit and this source/process analysis after framework migration. The distinct [Epic 5 hold and staging/device gates](../PLAN.md) remain open.

Because this current source snapshot found no external direct caller and the scoped Release process loaded no forge file, the next engineering slice should address the documented CI action/runtime warnings, followed by New Architecture readiness. This is a priority choice, not a safety classification; revisit `node-forge` sooner if a caller or new advisory evidence appears.
