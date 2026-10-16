# Scene Review image annotation guide

**Schema version:** `scene-review-v2`
**Status:** Pilot guidance; no rights-approved image source or pilot labels exist.

This guide describes only what is visible in one image. Annotators must not
infer safety, structural capacity, or a hazard's active state. The current
dataset rights gate is recorded in `docs/data-sources.md`; do not collect,
download, annotate, or train on pending/excluded images. Uploaded Scene Review
images are transient inference inputs and must not be copied into the training
set.

## Label IDs

The indexed-mask IDs are fixed and reserved as follows:

| ID | Label | What to mark |
| --- | --- | --- |
| `0` | `open_ground` | Visible floor or ground surface that appears unobstructed in the image. This is a visual surface label, not a safety or accessibility claim. |
| `1` | `obstacle` | Visible object, debris, or obstruction occupying or crossing a ground area. |
| `2` | `glass_facade` | Visible exterior glass or window-pane surfaces on a building. |
| `3` | `overhead_lines` | Visible overhead wires or cables only; their type is not inferred. |
| `4` | `visible_building_damage` | Directly visible physical damage to a building surface, using the boundaries below. |
| `5` | `background` | Every clearly visible, labelable non-target pixel, including identifiable people and other ordinary scene content. This is a mask annotation value, never a displayed or predicted class. |
| `255` | `ignore` | Only genuinely ambiguous, occluded, or otherwise unlabelable pixels. Exclude these pixels from supervised loss and agreement denominators. |

These are canonical single-class indexed masks: each pixel has one ID. Do not
invent additional IDs. `ignore` takes precedence where a boundary or identity
is uncertain. A run may declare a supported subset of the five target classes.
For that run, convert pixels labeled with any unsupported canonical target ID
to `ignore` (`255`), never to `background` (`5`). Preserve and hash the
canonical source mask; apply this conversion to the run-specific mask before
target generation, loss, or evaluation. Background pixels do not create DETR
segmentation targets; unmatched DETR queries represent background.

## General pixel rules

- Annotate only visible pixels in the supplied frame. Do not complete objects
  behind occluders or outside the image.
- Assign clearly visible non-target content to `background`, including people,
  clothing, walls, sky, vegetation, and ordinary objects that do not meet a
  target definition. Do not use `ignore` as a catch-all for out-of-scope content.
- Trace the visible edge of an object/surface at the source image resolution.
  Include antialiased boundary pixels only when their visible content clearly
  belongs to that class; assign uncertain mixed pixels to `ignore`.
- Leave a narrow uncertain seam as `ignore` rather than forcing adjacent
  classes to meet. Do not dilate masks to make them look smoother.
- Shadows, reflections, color changes, perspective, or an object's apparent
  distance alone do not establish a class.
- Do not label text, signs, overlays, UI elements, watermarks, or synthetic
  annotations as scene content. Mark such pixels `ignore` if they obscure the
  underlying scene.
- If image quality prevents a stable distinction, use `ignore` for the
  affected region and record the reason in the annotation notes.
- A physical object that occludes a labeled surface takes the pixel at its
  visible silhouette. For overlapping non-ground classes, use the visible
  foreground class; if class identity is uncertain, use `ignore`.

## Class boundaries

### `open_ground` (0)

Include visible floor/ground surfaces in indoor or outdoor scenes: tile,
concrete, asphalt, stone, wood flooring, compacted earth, or grass when the
surface is visible and not occupied by an object. Include paved plazas,
sidewalks, paths, road surfaces, and open indoor floor. Mark only the pixels
belonging to the surface plane, following visible perspective boundaries.

Exclude people, vehicles, furniture, debris, vegetation standing above the
surface, curbs/walls, stairs' vertical faces, water, holes, and surfaces hidden
by objects. A curb top or stair tread may be open ground only if clearly a
walkable-looking horizontal surface in the image; this label still makes no
claim about actual accessibility. Do not infer a clear region behind an
occlusion. If the material/surface boundary or its visible extent cannot be
reliably traced, mark it `ignore`.

### `obstacle` (1)

Include visible solid objects and debris that occupy or cross a ground/floor
area: furniture, bags, vehicles, fallen masonry, rubble, branches, and similar
items. Trace the visible silhouette, including visible parts over a ground
surface. People are not an `obstacle` target in this schema; clearly visible
people and clothing are `background`.

Exclude shadows, reflections, painted markings, texture, and distant objects
that do not visibly occupy/cross a ground area. Do not label something an
obstacle based on a guessed future path or danger. If a thin, partly hidden, or
motion-blurred object cannot be outlined consistently, use `ignore`.

### `glass_facade` (2)

Include visible exterior window panes or curtain-wall glass that can be
distinguished as façade glazing. Trace pane surfaces, not the whole building;
exclude opaque frames, mullions, walls, and interior objects visible through
the glass. Include reflections only within an already identifiable pane
surface. If glass cannot be distinguished from reflective metal, dark openings,
or sky reflections, use `ignore`.

This label means only that glass is visible in the frame. Never label or infer
reinforced/weak construction, glass fragility, falling-glass risk, or a safe
distance from the building.

### `overhead_lines` (3): visible overhead wires or cables only

Include visible overhead wires or cables whose line-like physical structure can
be followed in the image. Trace the visible wire/cable pixels at native
resolution; if it is thinner than a stable pixel trace, mark its uncertain
pixels `ignore` rather than drawing an expanded line. Exclude poles, towers,
antenna elements, building edges, cables on the ground, and indistinguishable
background lines. If wires cross and cannot be separated, mark the crossing
`ignore`.

The model does not identify whether a wire or cable is electrical, utility,
communications, or another type. It also does not identify voltage, whether it
is energized/live, whether it is damaged, or whether it presents electrical
danger.

### `visible_building_damage` (4)

Include only clearly visible physical damage on a building surface: a visible
crack with a discernible discontinuity, missing/broken façade material, a
collapsed or displaced portion, or an exposed damaged structural element.
Outline only the visible damaged pixels, not the entire building or a guessed
damage footprint. A crack too fine to trace reliably is `ignore`.

Exclude ordinary joints, seams, stains, shadows, reflections, normal texture,
construction features, and any condition that requires engineering judgment to
call damage. Do not label a building reinforced, earthquake-resistant,
structurally unsafe, or likely to fail. This class records visible appearance
only and is not a structural assessment.

## Ignore and scene inclusion rules

Use `ignore` only for genuinely unlabelable pixels, such as an occluded
boundary, severe blur, an ambiguous target identity, or a UI/text overlay that
hides the scene. A small or out-of-scope item that is still clearly visible is
`background`, as are identifiable people. Assign every other visible,
labelable non-target pixel `background` (`5`). This value is
used only in indexed masks and is omitted when constructing DETR targets; it
must never appear as an inference class. In canonical annotation masks, use
`ignore` (`255`) for ambiguous, occluded, or otherwise unlabelable pixels. In a
run-specific mask, also replace every canonical target pixel whose class is
unsupported by that run with `ignore`; never replace it with `background`.

The first implementation uses the stock DETR mask loss, which treats pixels
outside target masks as negatives and cannot safely apply an ignore mask at
pixel level. Therefore, exclude an entire sample whose run-specific mask
contains any `ignore` pixel, including pixels remapped from unsupported
canonical classes, from both training loss and validation loss. Record
unsupported-pixel counts by canonical class, total samples, samples containing
run-specific ignore pixels, loss-eligible samples, and samples excluded from
loss for the training and validation splits in artifact metadata. Record those
pixel/sample counts plus total and evaluated sample counts for the test split.
Evaluation metrics mask out run-specific `ignore` pixels, including pixels
remapped from unsupported classes. Stop training if the remapped pixels and
resulting sample exclusions leave fewer examples than the declared minimum
needed for training, validation, or required evaluation slices; do not
silently drop samples or count unsupported pixels as background.

Before full annotation and training, predeclare with the feature owner the
maximum acceptable ignore-driven sample exclusion rate, minimum retained sample
counts, and required scene/source coverage. On the double-annotated pilot,
report for each proposed supported-label subset and split the total sample
count, samples with at least one run-mask ignore pixel, excluded count and rate
(`excluded / total`), retained count, and counts/rates by relevant scene/source
slice. Do not invent thresholds after seeing results. Stop and revise the
annotation guidance, data collection, or loss handling if the declared rate is
exceeded, retained data is insufficient, or exclusions make examples
unrepresentative; do not recode genuinely ambiguous pixels as background to
pass the gate.

Include suitable rights-approved indoor and outdoor scenes with varied surface
types, viewpoints, lighting, occlusion, image quality, and ordinary as well as
post-event conditions. Record source, location/event/capture group, setting,
lighting, occlusion, and quality metadata when known. Do not imply Philippine
coverage unless source geography supports that claim. Exclude images with
unclear provenance, disallowed terms, personal/private content without a lawful
basis, or user uploads lacking explicit separate training consent.

## Double-annotation pilot and adjudication

Before full annotation, select a small, rights-approved pilot that spans the
available indoor/outdoor settings and difficult boundaries. Two annotators
independently label every pilot image from the same source pixels using this
guide and schema version. They must not see each other's masks before both are
submitted. Record annotator IDs, guide version, image/source IDs, completion
date, and tool/version; do not put private image paths or pixels in reports.

Define jointly labelable pixels as pixels where neither annotator's mask is
`ignore`. Compute the pixel agreement rate, per-class intersection-over-union,
and confusion counts only on these jointly labelable pixels. Separately report
the one-sided-ignore disagreement count and fraction of all image pixels
(exactly one mask is `ignore`), the both-ignore coverage count and fraction of
all image pixels (both masks are `ignore`), and jointly labelable count and
fraction of all image pixels. Also report disagreement examples by category:
boundary placement, class
identity, visibility/occlusion, omitted small/thin object, or guide ambiguity.
Do not silently remove one-sided-ignore pixels from the review; report them as
annotation disagreement. Do not collapse classes into a single headline score
that can conceal poor agreement for a sparse class.

An adjudicator reviews disagreements against the image and this guide, records
the resolution and rationale, and updates the guide when a recurring ambiguity
requires a rule change. If a class cannot be applied consistently, mark it
unsupported for the pilot/training run, revise the guide, and repeat the
double-annotation check on new examples before expanding annotation. Preserve
both original masks and the adjudicated mask outside Git under the approved
data controls. The pilot measures annotation consistency only; it is not model
quality evidence. Set numeric agreement gates with the feature owner before
full annotation, not after inspecting the held-out test set.

## Safety and review language

The labels describe visible pixels. They do not certify a safe zone, a
reinforced plaza, a structurally sound building, an accessible route, or a
hazard's likelihood or current state. In particular, the schema forbids labels
for reinforcement, overall safety, energized/live wires, and actual or
imminent falling-glass risk. Any product output must retain these limits and
present open-ground predictions as visual candidates for human review.
