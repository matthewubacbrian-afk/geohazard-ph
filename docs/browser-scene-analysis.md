# Browser Scene Review

## Purpose And Cost Boundary

The web `/scene-analysis` page analyzes a captured JPEG in a local module worker.
It does not upload the picture, call an inference provider, or fall back to the
Python analysis endpoint. There is no per-picture inference charge or API key.
Model download availability and device capacity can still limit the feature.
Ordinary web hosting bandwidth and the user's internet/device usage still exist;
this does not change provider free-plan quotas or guarantee unlimited hosting.

```text
First use: browser <- public, versioned JS/WASM/model downloads
Each picture: camera -> JPEG in page memory -> local worker -> local evidence UI
              (no image request to Render, Supabase, Upstash, or Hugging Face)
```

The default Render API can continue returning `scene_analysis_unavailable` (503):
it still lacks the server model package and weights. That endpoint is no longer
the web page's default analysis path. The mobile client retains its existing
server path and is not made operational by this web change.

## Pinned Runtime And Model

- Runtime: [Transformers.js](https://huggingface.co/docs/transformers.js/v3.8.1/index)
  3.8.1, full browser bundle from
  `https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/dist/transformers.min.js`.
  The `.web.min.js` build has bare imports and is not used as a direct worker URL.
- WASM files: `onnxruntime-web@1.22.0-dev.20250409-89f8206ba4/dist/` on jsDelivr,
  matching that runtime's dependency version. One thread, WASM proxy disabled.
- Model: [Xenova/detr-resnet-50-panoptic](https://huggingface.co/Xenova/detr-resnet-50-panoptic),
  revision `ea24b2d4e0bfae31f0a1299ba3fb892a2df064de`, q8 weights
  `onnx/model_quantized.onnx` (44,483,407 bytes). The
  [base model card](https://huggingface.co/facebook/detr-resnet-50-panoptic)
  lists Apache-2.0 and explains its general COCO panoptic training and limitations.
- Label provenance: official [COCO panoptic categories](https://github.com/cocodataset/panopticapi/blob/cf0760099461dfd87e284e768bc43cfbf733c871/panoptic_coco_categories.json).
  The converted config leaves categories 184-200 as `LABEL_<id>` placeholders.
  The browser resolves those 17 names from this pinned category file. Recognized
  cues retain the official merged names; floor-other-merged, pavement-merged,
  and grass-merged map to the existing candidate classes floor-other, pavement,
  and grass. Other unknown placeholder labels are omitted.

Model weights are cached by Transformers.js in browser storage where supported;
the worker also reuses the loaded model across analysis requests on the page.
Cache eviction/private browsing may require another download. First use requires
internet access, downloads model weights plus runtime files, and can be slow.
No paid Hugging Face endpoint or token is configured. Public downloads can fail
or be throttled; that produces an unavailable message rather than paid fallback.

## Processing And Lifecycle

`web/src/services/browserSceneAnalysis.ts` owns a lazy worker. It permits one
analysis at a time, forwards progress, terminates on cancellation/unmount/failure,
and has a three-minute timeout. Retaking a picture aborts in-progress analysis.
Photos/results are not persisted by this service; browser cache stores model
assets, not captures. The existing camera preview is cleared on retake/exit.

The worker validates bounded JPEG input (4 MiB encoded image budget, captured
edge at most 1600 pixels), then reduces the image to at most 512 pixels per edge.
The provisional blur cue uses grayscale Laplacian variance below 400, with the
existing explicit continue/retake choices. It is not a calibrated reliability
measurement. Model preprocessing uses shortest edge 384 / longest edge 512 to
bound device work. These settings and quantization differ from server inference;
the browser model version includes `q8:browser-512:coco-cf076009`.

Numeric segmentation scores are retained without inventing confidence. Candidate
surface masks need score >= 0.5. Four-connected components smaller than 1% of the
processed image are excluded. Outer contours are simplified to at most 64 points;
they do not represent enclosed holes/objects. Area fraction uses actual component
pixels, not the filled outline. The UI explicitly explains that simplified
outlines may include objects or gaps and are not evidence of safety.

The five largest-ranked candidates use the existing heuristic:
`relative area * 0.50 + compactness * 0.30 + model confidence * 0.20`.
This orders visual review; it is not a safety probability, an obstruction check,
or a calibrated geohazard assessment. Existing fixed scene limitations remain.

## Verification And Operation

- Run `npm test` and `npm run build` from `web/` for unit/UI/build verification.
  Tests use injected workers/masks and do not download models or call live APIs.
- For actual runtime acceptance, open the page in a supported modern browser,
  allow the camera, capture a well-lit scene, and choose Analyze image. Test the
  blur choice, a no-candidate scene, a visible ground scene, repeat analysis,
  retake during processing, and navigation away.
- In browser network tools, confirm only model/runtime GET requests occur and
  there is no picture POST or `/api/v1/scene-analyses` request. Repeated analysis
  should reuse the warm model; a new browser/profile may need the initial files.
- If analysis fails, check public CDN/model downloads, available device memory,
  browser compatibility and the timeout. Do not enable a paid fallback. The UI
  provides safe retry guidance without logging image data or raw exceptions.
- Deploy only the web change through Render Static Site. No database migration,
  new provider, API model container, or worker-image change is required.

2026-11-05 local production-build checks in headless Microsoft Edge used public
test photographs (not user captures). The [model-documentation cats photo](https://huggingface.co/datasets/Xenova/transformers.js-docs/resolve/main/cats.jpg) produced
cat/couch/remote cues. An [ADE20K fixture photo](https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg) produced a grass candidate plus
grass/house/sky/tree/wall cues after the taxonomy fix. The outdoor run took about
22 seconds cold and eight seconds warm. Network capture observed zero HTTP writes
and zero additional weight requests on repeat. These timings are device-specific;
the test verifies the path, not model accuracy or physical mobile performance.
ONNX Runtime emitted a non-fatal dynamic-output-shape warning during these runs.
Physical phone performance and broad real-scene accuracy remain unverified.

A separate blank-JPEG browser check displayed the blur choices before any model
weight request, made zero HTTP writes, and cleared the preview on retake. These
checks used a fake camera feed and explicit public/synthetic fixtures; physical
camera quality, phone memory limits, and adverse scene conditions still require
real-device evaluation.


## Staging Verification (2026-11-05)

[PR #89](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/89) merged as
`5415fe62c9ca6e1d369ab37d80a603b5de63b4c0`.
[Web CI](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/42026884501)
passed all 193 tests and the production build. Render served
`/assets/index-Z5B4pfKc.js` with the browser-analysis worker and privacy text.

An actual headless Edge run against the [public staging page](https://geohazard-ph-staging-web.onrender.com/scene-analysis)
used the public ADE20K fixture above through a fake camera capture. It displayed
one grass candidate and the recognized house/grass/sky/tree/wall cues. Cold/warm
analyses took about 25/11 seconds. Network interception observed zero HTTP writes
and no additional model-weight requests on repeat. This verifies deployed local
inference; it is not a physical-phone test or an accuracy evaluation.
