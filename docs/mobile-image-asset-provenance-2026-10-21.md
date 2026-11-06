# Mobile image asset provenance — 2026-10-21

This review follows the two `image-size` 1.2.1 rows in the [mobile advisory gate matrix](mobile-advisory-attack-path-gates-2026-10-21.md): [GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq) for JXL/HEIF boxes and [GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) for ICNS entries. It checks the current repository and pinned install for supported-extension image inputs and observes two local, non-published Metro bundles. It does not establish attacker control, exact CI call execution, or device inclusion. All 34 audit finding dispositions, including the `image-size` row with two direct advisory references, remain **undetermined**.

## Reproducible scope

The reviewed head used `react-native` 0.75.5, Metro 0.80.12, and `image-size` 1.2.1 from `mobile/package-lock.json`; `npm ci` completed against that lockfile. The earlier [consumer-call review](mobile-image-size-callsites-2026-10-20.md) locates Metro's `getAssetData` path/buffer call and `getAssetSize` buffer call. Metro checks the filename's image type before calling `image-size`, but the installed parser chooses JXL, HEIF, or ICNS handlers by file bytes. Therefore a supported suffix alone cannot rule out either advisory's crafted input.

The asset search used a conservative suffix set under `mobile/`: Metro's `isAssetTypeAnImage` types (`png`, `jpg`, `jpeg`, `bmp`, `gif`, `webp`, `psd`, `svg`, `tiff`, `ktx`), the common `tif` variant, and the advisory format suffixes (`jxl`, `heif`/`heic`, `icns`). This is broader than default Metro `assetExts`; TIFF and KTX are not default asset extensions. It used `rg --files --no-ignore` so the installed `node_modules` tree was included. Static `import`/`require` inspection of `mobile/index.js` and `mobile/src` found no image-file reference. All 10 tracked image files are Android `mipmap-*` launcher PNGs under native resources; the tracked iOS asset catalog has metadata but no image file. These native resources are separate from Metro asset modules.

| Installed asset owner | Supported-suffix files | Input role observed |
| --- | ---: | --- |
| `@react-native/debugger-frontend` | 225 | Bundled debugger frontend resources in the installed package; no corresponding image source in either local app bundle. |
| `react-native` | 11 | Five Android `devsupport` PNGs, five LogBox UI PNGs, and one NewAppScreen logo; none appeared as an image source in either local Release-like bundle. |
| `@react-native-community/cli-debugger-ui` | 6 | Debugger UI resources; no corresponding image source in either local app bundle. |
| `istanbul-reports`, `@jest/reporters`, `metro` | 5 total | Test/report or Metro integration-test assets; no corresponding image source in either local app bundle. |

The 247 installed supported-suffix files plus 10 tracked native PNGs yielded 257 candidates. Byte-prefix inspection found 43 PNG signatures and 214 SVG documents; none had a JXL, HEIF, or ICNS signature under those suffixes. This is a current-file inventory, not a promise about future dependency installs, generated files, `.zip/` assets, or asset paths supplied to Metro by another process.

## Non-published Metro observation

From `mobile/`, the pinned React Native CLI was run separately for Android and iOS with `--dev false --entry-file index.js`, `--bundle-output`, `--assets-dest`, and `--sourcemap-output` pointing under `%TEMP%/geohazard-image-assets-2026-10-21-<platform>/`. Android also used `--reset-cache`. Both commands exited successfully. Bundle files and maps stayed outside the repository; no `assets` directory was created for either platform.

| Local bundle | Source-map sources | Image-file sources | Copied assets | Package-name comparison with final PR #62 Release report |
| --- | ---: | ---: | ---: | --- |
| Android | 625 | 0 | 0 | Same set of 25 package names. |
| iOS | 621 | 0 | 0 | Same set of 25 package names. |

The package-name comparison used the repository's `scripts/mobile_artifact_inventory.py` source-name extraction on these local maps and the final PR #62 Android/iOS `mobile-artifact-report` JSON. The local map hashes are not the CI map hashes; the commands and build environments differ. The observations show no serialized image asset module in these two local app bundles and no current supported-suffix file whose inspected prefix selects the affected JXL/HEIF or ICNS handlers. They do **not** trace every `getAssetSize` caller, prove that `image-size` was never loaded by a build process, or classify the installed dependency as build-only or safe.

A disposition change would still need a controlled-input route to a supported-suffix path or buffer containing the advisory's crafted structure, execution of the affected parser operation in the relevant process, and its error/timeout effect. Exact-head CI instrumentation or an equivalent build trace would be needed to assert which Metro calls execute there. Device attribution needs the actual app execution path; neither an absent source-map package name nor this local asset inventory is enough. Repeat the inventory after dependency or React Native migration and if new assets are introduced.
