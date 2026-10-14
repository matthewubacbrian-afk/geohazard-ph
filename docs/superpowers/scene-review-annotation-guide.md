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
| `3` | `overhead_lines` | Visible overhead electrical or utility wires/cables. |
| `4` | `visible_building_damage` | Directly visible physical damage to a building surface, using the boundaries below. |
| `5` | `background` | Every visible, labelable pixel that is outside the five target classes. This is a mask annotation value, never a displayed or predicted class. |
| `255` | `ignore` | Ambiguous, hidden, too small, or otherwise not reliably annotatable pixels. Exclude these pixels from supervised loss and agreement denominators. |

These are single-class indexed masks: each pixel has one ID. Do not invent
additional IDs. `ignore` takes precedence where a boundary or identity is
uncertain. A run may declare a supported subset of the five target classes,
but unsupported classes must not be counted as successful predictions or
silently converted to background. Background pixels do not create DETR
segmentation targets; unmatched DETR queries represent background.

## General pixel rules

- Annotate only visible pixels in the supplied frame. Do not complete objects
  behind occluders or outside the image.
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
surface. Include a person only if the project later explicitly declares human
occlusion as an obstacle class; under this schema people are `ignore` because
they are not a stable environmental obstruction category.

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

### `overhead_lines` (3)

Include visible overhead wires or cables whose line-like physical structure can
be followed in the image. Trace the visible wire/cable pixels at native
resolution; if it is thinner than a stable pixel trace, mark its uncertain
pixels `ignore` rather than drawing an expanded line. Exclude poles, towers,
antenna elements, building edges, cables on the ground, and indistinguishable
background lines. If wires cross and cannot be separated, mark the crossing
`ignore`.

This label does not identify voltage, whether a line is energized, whether it is
damaged, or whether it presents electrical danger.

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

Use `ignore` for occluded boundaries, severe blur, low resolution, glare,
darkness, compression artifacts, ambiguous class identity, tiny details below
stable annotation resolution, and any region covered by UI/text overlays.
Assign every other visible, labelable pixel `background` (`5`). This value is
used only in indexed masks and is omitted when constructing DETR targets; it
must never appear as an inference class. Use `ignore` (`255`) only for
ambiguous, occluded, or otherwise unlabelable pixels.

The first implementation uses the stock DETR mask loss, which treats pixels
outside target masks as negatives and cannot safely apply an ignore mask at
pixel level. Therefore, exclude an entire sample containing any `ignore` pixel
from both training loss and validation loss. Record total samples, samples
containing ignore pixels, loss-eligible samples, and samples excluded from loss
for the training and validation splits in artifact metadata. Record total,
ignore-containing, and evaluated sample counts for the test split. Evaluation
metrics mask out `ignore` pixels. Stop training if these
exclusions leave fewer samples than the declared minimum needed for training,
validation, or required evaluation slices; do not silently drop samples or
count ignored pixels as background.

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

For each class, report pixel intersection-over-union and class-wise agreement
on the union of pixels either annotator assigned to that class, along with
confusion counts and ignored-pixel coverage. Also report disagreement examples
by category: boundary placement, class identity, visibility/occlusion, omitted
small/thin object, or guide ambiguity. Exclude ignore pixels from these
calculations and report their share separately. Do not collapse classes into a
single headline score that can conceal poor agreement for a sparse class.

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
