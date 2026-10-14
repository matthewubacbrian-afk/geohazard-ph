# Scene Review — Vision Training Design

**Date:** 2026-10-15

## Problem

Scene Review currently uses a generic pretrained segmentation model to identify some floor and ground regions and common visual classes. It has no project-specific training data or training workflow, and it does not analyze the surrounding scene for the visible hazard cues shown in the feature concept. Its current output is not validated for local indoor, outdoor, or earthquake-response scenes.

The feature should help a person visually review a captured scene by highlighting open ground candidates, visible obstacles, and visible hazard cues around them. A camera image cannot establish that a plaza is reinforced, that a structure is sound, or that a location is safe during an earthquake. The model must report visual evidence and uncertainty without presenting a safety verdict.

## Goals

- Define reproducible, image-space annotation labels for visible open floor/ground, obstacles or debris, and supported visible hazard cues.
- Create an offline dataset and training pipeline that records source provenance, permissions, annotation version, split membership, input hashes, training configuration, and evaluation results.
- Train and compare a task-specific segmentation model against the current pinned pretrained model on a source-separated, held-out evaluation set.
- Evaluate each label independently and report segmentation quality, missed detections, false detections, and performance across relevant scene conditions.
- Export a versioned model artifact only after data rights, annotation quality, evaluation criteria, and runtime constraints are reviewed.
- Preserve the current transient-image privacy contract: uploaded user images are not retained or used for training.
- Keep Scene Review output framed as candidate areas and visible cues. The model must not emit or imply “safe spot,” structural reinforcement, earthquake resistance, falling-glass risk, or electrical safety.

## Non-goals

- Certifying or recommending an evacuation location, route, shelter, or safe zone.
- Inferring construction quality, reinforcement, structural integrity, ground stability, actual glass-fall probability, whether a wire is live, or conditions outside the captured image.
- Training from uploaded user images, collecting images without explicit reuse permission, or retaining user analysis history.
- Replacing official emergency guidance or making autonomous emergency decisions.
- Deploying a model before independent evaluation and API/runtime packaging review.

## Context And Constraints

- Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/testing-standards.md`, `docs/data-sources.md`, and `docs/glossary.md`.
- Epic 7 already defines transient still-image analysis, normalized image polygons, `candidate_regions[]`, `visual_cues[]`, deterministic ranking, and fixed limitations. This design extends the offline model and evaluation capabilities while retaining those contracts unless a later API design explicitly changes them.
- The current model is `facebook/detr-resnet-50-panoptic` at immutable revision `d53b52a799403a8867920f82c869e40732b47037`. It is a baseline, not a locally validated scene model.
- The existing `ml/` package trains tabular regional earthquake risk profiles. Scene image training must be isolated from that pipeline and must not mix image datasets or artifacts with regional risk-profile artifacts.
- There are no project-owned or project-approved scene image datasets in the repository. A public post-earthquake segmentation dataset is a possible research lead, but its damage/debris labels do not cover open ground, and image rights must be checked at the original-source level. A dataset card or code repository license alone is not sufficient evidence that source images may be used to train and distribute model weights.
- Only datasets whose terms permit the intended training, evaluation, and model-weight use may enter the pipeline. Record license/terms, source URL, retrieval date/version, attribution requirements, and any restrictions. If rights are unclear, exclude the data until reviewed.
- Split by source, location, event, or capture session before training so near-duplicate images cannot cross train/validation/test boundaries. Keep raw images, masks, and downloaded annotations out of Git.
- Image data should reflect both indoor and outdoor scenes and varied lighting, viewpoints, surface types, obstruction, and image quality. Report dataset coverage; do not imply that the data represents the Philippines unless it does.

## Alternatives Considered

1. **Fine-tune an existing segmentation model on approved scene labels (chosen).** This matches the requested open-area and surrounding-cue behavior while reusing pretrained visual features. It requires careful annotation and held-out evaluation; it does not make unsupported safety inferences.
2. **Keep the generic model and only adjust class filters/ranking.** This is cheaper and can improve presentation, but it cannot learn task-specific open-area boundaries or missing hazard cues from the feature concept.
3. **Train a scene-level “safe/unsafe” classifier.** Rejected because a still image cannot provide reliable ground truth for structural reinforcement, dynamic hazards, or actual safety; a binary label would overstate the available evidence.

## Design

### Architecture and data flow

```text
rights-reviewed image sources
  -> immutable dataset manifest and annotation guide
  -> source/location-grouped train, validation, and test splits
  -> image/mask validation and label mapping
  -> offline fine-tuning and baseline comparison
  -> per-class and slice evaluation report
  -> reviewed versioned artifact
  -> later backend integration under the existing SceneAnalysis contract
```

Training is an offline developer/maintainer workflow. The API never trains, downloads datasets, or downloads model weights while serving a request. Training inputs and generated artifacts live in ignored local paths or approved external storage; Git contains only code, small synthetic fixtures, and documentation.

### Annotation labels

The first annotation schema uses image-space masks and a documented annotation guide:

- `open_ground`: visible floor or ground surface that appears visually unobstructed in the captured pixels. This describes appearance only; it does not assert accessibility, stability, or safety.
- `obstacle`: visible object, debris, or obstruction occupying or crossing a candidate ground area.
- `glass_facade`: visibly identifiable exterior glass or window façade. This is a contextual visual cue, not a prediction of falling glass.
- `overhead_lines`: visible overhead wires or cables only. The model does not identify their type (electrical, utility, communications, or other), voltage, live/energized status, or danger.
- `visible_building_damage`: only damage patterns explicitly defined in the annotation guide and reliably identifiable from the image. This label must not be mapped to “structurally unsafe” or used as a proxy for reinforcement.
- `background` (mask ID `5`): every visible, labelable pixel outside the five target classes. It is an annotation value only and is never a displayed or predicted class.
- `ignore` (canonical mask ID `255`): ambiguous, occluded, low-resolution, or otherwise unlabelable pixels. In a run-specific mask, pixels assigned to canonical target classes unsupported by that run are also mapped to `255`, never to background; report these remapped pixels separately.

This is annotation schema version 2 (`scene-review-v2`), superseding the initial draft. Mask IDs are `0=open_ground`, `1=obstacle`, `2=glass_facade`, `3=overhead_lines`, `4=visible_building_damage`, `5=background`, and `255=ignore`. Annotators label what is visible, not inferred hazard state. If a target class cannot be consistently distinguished in a pilot annotation review, exclude it from the trained label set rather than encoding guesses. For double annotation, compute pixel agreement, per-class IoU, and confusion counts only on pixels where neither mask is ignore; separately report counts and fractions of one-sided-ignore disagreement, both-ignore coverage, and jointly labelable coverage using all image pixels as the coverage denominator. At least a reviewed sample must be double-annotated, with agreement and adjudication outcomes reported before full training.

For each run, build a run-specific mask from the canonical annotation mask and its declared supported target subset: replace every pixel whose canonical target class is unsupported in that run with `ignore` (`255`), never `background` (`5`). Preserve and hash the canonical source mask. Count remapped pixels by canonical class and count all samples containing run-specific ignore pixels, including original ignore labels and remapped unsupported classes. For DETR target conversion, create instances only for supported target classes; omit `background` regions so unmatched DETR queries represent background. The first implementation uses the stock mask loss, which treats pixels outside target masks as negatives and cannot safely ignore selected pixels. Exclude any whole sample whose run-specific mask contains one or more `ignore` pixels from both training loss and validation loss. Record, for training and validation, total samples, per-class unsupported-pixel counts, ignore-containing samples, loss-eligible samples, and loss-excluded samples in artifact metadata; for test, record the same pixel/sample counts plus total and evaluated sample counts. Evaluation metrics mask out run-specific ignore pixels, including remapped unsupported classes. Stop before training or acceptance if remapping and resulting exclusions leave fewer examples than the declared minimum for a split, class, or required scene slice.

### Model and result mapping

- Fine-tune a segmentation architecture with a pinned pretrained initialization. Select the implementation after checking its license, CPU inference cost, model size, and compatibility with the current backend runtime. The existing DETR model remains the baseline for comparison.
- Produce image-space masks for trained classes. Map open-ground components into the existing normalized `candidate_regions[]` polygons and map obstacle/hazard detections into `visual_cues[]` with class, confidence, and image-space location. Preserve the current response contract unless implementation requires a separately reviewed contract change.
- Any ranking adjustment may use documented visual evidence such as candidate area and visible overlap/proximity to detected cues. A ranking score remains an ordering aid, not a probability of safety. Do not label green overlays or candidates as “safe.”
- Include model artifact version and fixed limitations. Low-confidence or ambiguous predictions should be omitted or presented as uncertain according to a threshold calibrated on validation data and reported on held-out data.

### Dataset and artifact provenance

Each dataset manifest records source name and URL, license/terms evidence, attribution, version or retrieval date, permitted uses, image and mask counts, hashes, label schema version, annotation process, supported target subset, and source/location split assignments. Training metadata records code revision, dependency/runtime versions, initialization model revision, random seed, image preprocessing, hyperparameters, dataset manifest hash, per-split remapped unsupported-pixel counts by class, ignore/loss/evaluation sample counts described above, and metrics. Never store user-uploaded images or absolute local paths in public metadata.

### Evaluation and acceptance thresholds

Before final training, define minimum per-class metrics and acceptable false-positive/false-negative trade-offs with the feature owner. Evaluate at minimum per-class mask IoU and precision/recall, candidate-region coverage, and false visual-cue rate. Report performance by indoor/outdoor setting, lighting, occlusion, image quality, and source/location where sample counts permit. Compare against the pinned pretrained baseline on the same held-out examples. Do not choose thresholds on the test set.

The prototype is not eligible for API integration unless:

- Dataset rights and model-weight use are documented and reviewed.
- Annotation agreement and class coverage meet the thresholds declared before training.
- The trained model improves the agreed task metrics over the baseline without unacceptable regressions in any required scene slice.
- The model artifact can be loaded locally without network access, and backend resource/latency limits are measured.
- Product copy and result mapping retain the visual-candidate and limitations language.

If suitable licensed images or enough labeled examples cannot be obtained, stop at a documented data-readiness report; do not substitute synthetic images as evidence of real-scene performance.

### Error handling

Dataset validation fails closed for missing provenance, invalid masks, unknown labels, duplicate leakage across splits, or disallowed license status. Training fails with a clear diagnostic for missing data, incompatible masks, or invalid configuration. Evaluation must not silently omit a class or scene slice with insufficient samples; it reports the gap. Artifact export refuses to overwrite an existing version and includes a manifest checksum.

### Privacy and safety copy

Captured user images remain transient inputs to inference and are not copied into the training dataset. UI and API language uses “candidate open area” and “visible cue.” It does not state that a place is safe, reinforced, structurally sound, or a verified evacuation zone. Any contextual warning is limited to a visible cue in the frame and explains uncertainty.

## Rollout

Implement in gates: (1) source/rights inventory and annotation guide, (2) rights-reviewed pilot dataset and agreement review, (3) offline baseline/training/evaluation pipeline, (4) model review and resource measurement, and (5) a separate integration change only after acceptance criteria pass. No production model is enabled as part of the training-pipeline work alone. Keep the existing model behavior available until a reviewed artifact is explicitly selected.

## Files

- `docs/glossary.md` — canonical meaning of visible hazard cue and training provenance terms.
- `docs/data-sources.md` — approved image datasets and their source-level reuse terms, only after review.
- `ml/src/ml/scene_review/` — isolated dataset validation, training, evaluation, and export modules; no coupling to tabular risk-profile code.
- `ml/tests/` — deterministic tests for manifests, label/mask validation, split leakage, metrics, and artifact metadata using tiny synthetic fixtures.
- `ml/data/` and `ml/model_artifacts/` — ignored local paths for source images, masks, and trained weights; no raw or generated dataset/model files committed.
- `backend/app/services/scene_analysis_model.py` — later model adapter update only after model acceptance and a separate integration review.
- `web/src/pages/SceneAnalysis.tsx` and mobile Scene Review screen — later user-facing cue and limitation presentation, only if response mapping changes.
- `docs/project-status.md` — training/data readiness and evaluation evidence after work is completed.

## Testing Strategy

- ML unit tests use tiny local image/mask fixtures and no network or credentials. Cover license/provenance validation, supported label mapping, background and ignore IDs, invalid mask dimensions and class IDs, duplicate/source leakage detection, ignore-sample exclusion from training/validation loss, ignore-masked evaluation metrics, deterministic training configuration, metric calculations, insufficient-sample reporting, and immutable artifact export metadata.
- A small end-to-end pipeline test trains on synthetic fixtures into `tmp_path`; it validates pipeline mechanics only and is never reported as model-quality evidence.
- A separate evaluation run uses the rights-reviewed held-out real-scene data and records the exact manifest/model/code hashes, metrics, runtime, and limits. It is an explicit offline maintainer command, not a CI network test.
- If later API integration occurs, add backend service/API regression tests and run backend verification per `docs/testing-standards.md` in that integration change.

## Acceptance Criteria

- [ ] Annotation guide defines visible target classes, background and ignore IDs, boundaries, sample-level ignore-loss exclusions, and forbidden inferred claims.
- [ ] Every training/evaluation image has source-level terms and provenance sufficient to establish intended use; excluded data cannot enter a run.
- [ ] Dataset manifests and source/location-grouped splits are deterministic and detect duplicate leakage.
- [ ] Training and evaluation run offline from a pinned manifest and configuration; tests require no live network or credentials.
- [ ] Evaluation reports per-class metrics, false detections, scene-condition slices, baseline comparison, and data coverage limitations.
- [ ] Evaluation thresholds are declared before the final held-out run and are met before artifact approval.
- [ ] Artifact metadata is complete, versioned, hash-addressed, and exported without raw images or user image content.
- [ ] Model outputs are visible cues and open-area candidates only; no safe-place or structural certification is emitted.
- [ ] Runtime and latency are measured before any backend or deployment integration.
- [ ] Project status clearly distinguishes a synthetic pipeline test from real-scene model validation.

## Out Of Scope (backlog)

- Collecting a large Philippine scene dataset; this requires a separate consent, collection, and governance plan.
- On-device inference, video or multi-frame analysis, route planning, maps of certified shelters, and official evacuation guidance.
- Estimating structural engineering properties or dynamic glass/electrical hazards from pixels.
- Changing the public SceneAnalysis API contract or enabling the trained model in production; both require a separate integration review after evaluation.

## Spec self-review

- No placeholders remain. All labels explicitly separate visible evidence from inferred safety state.
- Goals map to acceptance criteria, and data rights are a gate before training or weight distribution.
- The plan scope is one offline training/data-readiness increment; backend integration is explicitly deferred until the model passes its gates.
- The current SceneAnalysis contract is retained, with any necessary response change deferred to a separate reviewed integration.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-15-scene-review-vision-training.md`
- Terminology: `docs/glossary.md`
- Existing feature design: `docs/superpowers/specs/2026-10-13-epic7-scene-analysis-design.md`
