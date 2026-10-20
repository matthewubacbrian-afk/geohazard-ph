# Mobile image-size consumer-call review — 2026-10-20

This review narrows the two direct `image-size` 1.2.1 references in the
[mobile advisory path record](mobile-advisory-exposure-review-2026-10-20.md):
[GHSA-5p2g-fcmc-qvqq](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq)
for crafted JXL/HEIF boxes and
[GHSA-w3rx-r6r6-pgpr](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr)
for crafted ICNS entries. The advisories describe loops in the Node.js image
parser. This review does not show that an attacker can put such bytes in a
project asset or that this parser executes on a distributed phone. All 34
production-graph finding dispositions remain **undetermined**.

## Reproducible source scope

The tracked `mobile/package-lock.json` and lockfile-only production tree show
`react-native` 0.75.5 > `@react-native/community-cli-plugin` 0.75.5 > `metro`
0.80.12 > `image-size` 1.2.1. `metro-config` also reaches Metro 0.80.12.
The exact Metro and `image-size` npm tarballs were downloaded outside the
repository; their SHA-512 digests matched the lockfile `integrity` fields.
A recursive search of published Metro `src/*.js` files found one direct
`image-size` import, in
[`Assets.js` at v0.80.12](https://github.com/react/metro/blob/v0.80.12/packages/metro/src/Assets.js).

| Metro call | Input and gate visible in exact-version source | Evidence limit |
| --- | --- | --- |
| `getAssetSize(type, content, filePath)` calls `image-size(content)` | The exported helper first checks Metro's image-type list and rejects an empty `content` buffer. Its listed types are PNG, JPG/JPEG, BMP, GIF, WebP, PSD, SVG, TIFF, and KTX. | The helper is exported; callers outside the inspected Metro package and control of their buffers were not fully traced. |
| `getAssetData(assetPath, ...)` calls `image-size(isImageInput)` | Metro's [asset serializer](https://github.com/react/metro/blob/v0.80.12/packages/metro/src/DeltaBundler/Serializers/getAssets.js) passes asset-module paths from its dependency graph. `Assets.js` collects local asset files, checks the asset extension against the same image-type list, then passes the first file path to `image-size`; its `.zip/` branch passes file bytes. | This is a build/packager call path from local project or dependency assets. Who can control asset contents in each build environment is unverified. |

The extension list does not include `jxl`, `heif`, `heic`, or `icns`.
That does **not** exclude the advisory operations: the pinned
[`image-size` lookup](https://github.com/image-size/image-size/blob/v1.2.1/lib/index.ts)
selects a handler by byte signature rather than filename extension, and its
[detector](https://github.com/image-size/image-size/blob/v1.2.1/lib/detector.ts)
and [handler table](https://github.com/image-size/image-size/blob/v1.2.1/lib/types/index.ts)
include JXL, HEIF, and ICNS. A supported-extension asset containing crafted
bytes is a possible parser-input shape; this record has not shown such an
asset in a relevant build or a route for an attacker to supply one.

The Android/iOS Release source maps from PR #57 still list only
`react-native` among the 34 audit finding names. Those package-name counts
do not prove whether this build-host code ran or whether any native or DEX
code is affected. The two `image-size` references and inherited chain rows
remain **undetermined**. A later attack-path review must check the full set
of asset producers and build inputs, then repeat this inspection after the
supported React Native migration.
