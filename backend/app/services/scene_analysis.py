"""Bounded image decoding and deterministic scene candidate ranking."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO
from math import hypot, isfinite, pi
from typing import Literal, Protocol

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGE_EDGE = 4096
MAX_IMAGE_PIXELS = 12_000_000
MIN_COMPONENT_FRACTION = 0.01
MIN_MODEL_CONFIDENCE = 0.50
MIN_SHARPNESS_SCORE = 400.0  # Provisional until held-out real-image calibration is recorded.
MAX_CANDIDATES = 5
MAX_POLYGON_POINTS = 64

CANDIDATE_CLASSES = frozenset(
    {
        "floor-other",
        "floor-stone",
        "floor-tile",
        "floor-wood",
        "ground-other",
        "road",
        "pavement",
        "grass",
        "gravel",
    }
)


class InvalidSceneImage(ValueError):
    """The input is not a supported, bounded JPEG image."""


class SceneAnalysisUnavailable(RuntimeError):
    """Scene segmentation is unavailable."""


class SceneImageQualityWarning(RuntimeError):
    """The image may be too blurry for reliable visual cue extraction."""

    def __init__(self, sharpness_score: float) -> None:
        super().__init__("The image may be blurry")
        self.sharpness_score = sharpness_score


@dataclass(frozen=True)
class PanopticSegment:
    class_name: str
    mask: np.ndarray
    model_confidence: float


class PanopticSegmenter(Protocol):
    def segment(self, image: Image.Image) -> Sequence[PanopticSegment]: ...


@dataclass(frozen=True)
class ImagePoint:
    x: float
    y: float


@dataclass(frozen=True)
class CandidateRegion:
    rank: int
    surface_class: str
    polygon: tuple[ImagePoint, ...]
    area_fraction: float
    compactness: float
    model_confidence: float
    ranking_score: float


@dataclass(frozen=True)
class VisualCue:
    class_name: str
    model_confidence: float


@dataclass(frozen=True)
class SceneAnalysisResult:
    result_status: Literal["candidates_found", "no_clear_candidate"]
    candidate_regions: tuple[CandidateRegion, ...]
    visual_cues: tuple[VisualCue, ...]


def decode_scene_image(image_bytes: bytes, mime_type: str) -> Image.Image:
    """Decode a bounded JPEG, apply EXIF orientation and discard source metadata."""
    if mime_type != "image/jpeg" or not isinstance(image_bytes, bytes):
        raise InvalidSceneImage("Only JPEG images are supported")
    if not image_bytes.startswith(b"\xff\xd8\xff"):
        raise InvalidSceneImage("The image is not a valid JPEG")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise InvalidSceneImage("The JPEG exceeds the decoded image size limit")

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.format != "JPEG":
                raise InvalidSceneImage("Only JPEG images are supported")
            width, height = source.size
            if width <= 0 or height <= 0:
                raise InvalidSceneImage("The JPEG has invalid dimensions")
            if max(width, height) > MAX_IMAGE_EDGE or width * height > MAX_IMAGE_PIXELS:
                raise InvalidSceneImage("The JPEG dimensions exceed the supported limits")
            source.load()
            oriented = ImageOps.exif_transpose(source)
            rgb = oriented.convert("RGB")
            clean = Image.new("RGB", rgb.size)
            clean.paste(rgb)
            return clean
    except InvalidSceneImage:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise InvalidSceneImage("The JPEG could not be decoded") from exc


def estimate_sharpness(image: Image.Image) -> float:
    """Return grayscale Laplacian variance after reducing the longest edge to 512 px."""
    grayscale_image = image.convert("L")
    grayscale_image.thumbnail((512, 512), Image.Resampling.BILINEAR)
    grayscale = np.asarray(grayscale_image, dtype=np.float32)
    if grayscale.shape[0] < 3 or grayscale.shape[1] < 3:
        return 0.0
    center = grayscale[1:-1, 1:-1]
    laplacian = (
        grayscale[:-2, 1:-1]
        + grayscale[2:, 1:-1]
        + grayscale[1:-1, :-2]
        + grayscale[1:-1, 2:]
        - 4 * center
    )
    return float(np.var(laplacian, dtype=np.float64))


def analyze_scene(
    image: Image.Image,
    segmenter: PanopticSegmenter,
    *,
    accept_quality_warning: bool = False,
) -> SceneAnalysisResult:
    """Extract and rank bounded surface components from injected panoptic masks."""
    sharpness_score = estimate_sharpness(image)
    if sharpness_score < MIN_SHARPNESS_SCORE and not accept_quality_warning:
        raise SceneImageQualityWarning(sharpness_score)
    segments = segmenter.segment(image)
    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive")
    image_area = width * height

    cue_confidences: dict[str, float] = {}
    components: list[tuple[str, int, int, int, int, float, float, np.ndarray]] = []
    for segment in segments:
        confidence = float(segment.model_confidence)
        if segment.class_name and isfinite(confidence) and 0 <= confidence <= 1:
            cue_confidences[segment.class_name] = max(
                confidence, cue_confidences.get(segment.class_name, 0.0)
            )

        if (
            segment.class_name not in CANDIDATE_CLASSES
            or not isfinite(confidence)
            or not 0 <= confidence <= 1
            or confidence < MIN_MODEL_CONFIDENCE
        ):
            continue
        mask = np.asarray(segment.mask, dtype=bool)
        if mask.shape != (height, width):
            raise ValueError("Segment masks must match the image dimensions")
        labels, connected = _label_components(mask)
        for label, pixel_area, perimeter, top_left in connected:
            compactness = min(4 * pi * pixel_area / (perimeter * perimeter), 1.0)
            components.append(
                (
                    segment.class_name,
                    label,
                    pixel_area,
                    perimeter,
                    top_left,
                    confidence,
                    compactness,
                    mask,
                )
            )
        del labels

    largest_area = max((item[2] for item in components), default=1)
    ranked: list[tuple[float, int, int, int, str, float, float, float, np.ndarray, int, int, int]] = []
    for (
        class_name,
        label,
        pixel_area,
        perimeter,
        top_left,
        confidence,
        compactness,
        mask,
    ) in components:
        area_fraction = pixel_area / image_area
        score = (
            min(pixel_area / largest_area, 1.0) * 0.50
            + compactness * 0.30
            + confidence * 0.20
        )
        top, left = divmod(top_left, width)
        ranked.append(
            (
                score,
                pixel_area,
                top,
                left,
                class_name,
                area_fraction,
                compactness,
                confidence,
                mask,
                label,
                top_left,
                perimeter,
            )
        )

    ranked.sort(key=lambda item: (-item[0], -item[1], item[2], item[3], item[4]))
    candidate_regions = []
    for index, item in enumerate(ranked[:MAX_CANDIDATES], start=1):
        _, _, _, _, _, _, _, _, mask, label, top_left, perimeter = item
        labels, _ = _label_components(mask)
        candidate_regions.append(
            CandidateRegion(
                rank=index,
                surface_class=item[4],
                polygon=_normalized_polygon(labels, top_left, width, height, perimeter, label),
                area_fraction=item[5],
                compactness=item[6],
                model_confidence=item[7],
                ranking_score=item[0],
            )
        )
    candidates = tuple(candidate_regions)
    cues = tuple(VisualCue(name, cue_confidences[name]) for name in sorted(cue_confidences))
    return SceneAnalysisResult(
        result_status="candidates_found" if candidates else "no_clear_candidate",
        candidate_regions=candidates,
        visual_cues=cues,
    )


def _label_components(
    mask: np.ndarray,
) -> tuple[np.ndarray, list[tuple[int, int, int, int]]]:
    """Label 4-connected raster runs without creating one Python object per pixel."""
    height, width = mask.shape
    labels = np.zeros(mask.shape, dtype=np.int32)
    capacity = max(min(height * 2, int(np.count_nonzero(mask)) + 1), 16)
    parent = np.zeros(capacity, dtype=np.int32)
    sizes = np.zeros(capacity, dtype=np.int32)
    perimeters = np.zeros(capacity, dtype=np.int32)
    top_lefts = np.full(capacity, height * width, dtype=np.int32)
    next_label = 1

    def ensure_capacity(required: int) -> None:
        nonlocal parent, sizes, perimeters, top_lefts, capacity
        if required <= capacity:
            return
        new_capacity = max(required, capacity * 2)
        parent = np.pad(parent, (0, new_capacity - capacity))
        sizes = np.pad(sizes, (0, new_capacity - capacity))
        perimeters = np.pad(perimeters, (0, new_capacity - capacity))
        top_lefts = np.pad(
            top_lefts,
            (0, new_capacity - capacity),
            constant_values=height * width,
        )
        capacity = new_capacity

    def find(label: int) -> int:
        root = label
        while parent[root] != root:
            root = int(parent[root])
        while parent[label] != label:
            following = int(parent[label])
            parent[label] = root
            label = following
        return root

    def union(first: int, second: int) -> int:
        first_root, second_root = find(first), find(second)
        if first_root == second_root:
            return first_root
        if sizes[first_root] < sizes[second_root]:
            first_root, second_root = second_root, first_root
        parent[second_root] = first_root
        sizes[first_root] += sizes[second_root]
        perimeters[first_root] += perimeters[second_root]
        top_lefts[first_root] = min(top_lefts[first_root], top_lefts[second_root])
        return first_root

    previous_starts = np.empty(0, dtype=np.int32)
    previous_ends = np.empty(0, dtype=np.int32)
    previous_labels = np.empty(0, dtype=np.int32)
    for y in range(height):
        row = mask[y]
        starts = np.flatnonzero(row & np.r_[True, ~row[:-1]]).astype(np.int32)
        ends = (np.flatnonzero(row & np.r_[~row[1:], True]) + 1).astype(np.int32)
        current_labels = np.empty(len(starts), dtype=np.int32)
        previous_exposed = np.zeros(len(previous_starts), dtype=np.int32)
        previous_index = 0
        for run_index, (start_value, end_value) in enumerate(zip(starts, ends)):
            start, end = int(start_value), int(end_value)
            ensure_capacity(next_label + 1)
            label = next_label
            next_label += 1
            parent[label] = label
            sizes[label] = end - start
            perimeters[label] = 2
            top_lefts[label] = y * width + start
            overlap_total = 0
            while (
                previous_index < len(previous_starts)
                and int(previous_ends[previous_index]) <= start
            ):
                previous_index += 1
            scan_index = previous_index
            root = label
            while scan_index < len(previous_starts) and int(previous_starts[scan_index]) < end:
                overlap = min(end, int(previous_ends[scan_index])) - max(
                    start, int(previous_starts[scan_index])
                )
                if overlap > 0:
                    overlap_total += overlap
                    previous_exposed[scan_index] += overlap
                    root = union(root, int(previous_labels[scan_index]))
                scan_index += 1
            root = find(root)
            perimeters[root] += end - start - overlap_total
            top_lefts[root] = min(top_lefts[root], y * width + start)
            current_labels[run_index] = label
            labels[y, start:end] = label

        for index, previous_label in enumerate(previous_labels):
            exposed = int(previous_ends[index] - previous_starts[index] - previous_exposed[index])
            if exposed:
                perimeters[find(int(previous_label))] += exposed
        previous_starts, previous_ends, previous_labels = starts, ends, current_labels

    for index, previous_label in enumerate(previous_labels):
        perimeters[find(int(previous_label))] += int(previous_ends[index] - previous_starts[index])

    roots = np.arange(next_label, dtype=np.int32)
    while True:
        compressed = parent[roots]
        if np.array_equal(compressed, roots):
            break
        roots = compressed
    flat_labels = labels.reshape(-1)
    chunk_size = 1_000_000
    for start in range(0, flat_labels.size, chunk_size):
        end = min(start + chunk_size, flat_labels.size)
        flat_labels[start:end] = roots[flat_labels[start:end]]

    minimum_area = (height * width + 99) // 100
    eligible = np.flatnonzero(
        (parent[:next_label] == np.arange(next_label)) & (sizes[:next_label] >= minimum_area)
    )
    components = [
        (
            int(label),
            int(sizes[label]),
            int(perimeters[label]),
            int(top_lefts[label]),
        )
        for label in eligible
        if label != 0
    ]
    return labels, components


def _normalized_polygon(
    labels: np.ndarray,
    top_left: int,
    width: int,
    height: int,
    perimeter: int,
    label: int,
) -> tuple[ImagePoint, ...]:
    start = (top_left % width, top_left // width)
    stride = max(1, (perimeter + 2047) // 2048)
    boundary = _trace_boundary(labels, label, start, stride, perimeter)
    tolerance = 1.0
    simplified = _douglas_peucker(boundary, tolerance)
    if len(set(simplified[:-1])) < 4:
        simplified = _douglas_peucker(boundary, 0.0)
    while len(simplified) > MAX_POLYGON_POINTS - 1:
        tolerance *= 1.5
        simplified = _douglas_peucker(boundary, tolerance)
    if len(set(simplified[:-1])) < 4:
        vertices = list(dict.fromkeys(boundary[:-1]))
        simplified = [vertices[index * len(vertices) // 4] for index in range(4)]
        simplified.append(simplified[0])
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return tuple(ImagePoint(x / width, y / height) for x, y in simplified)


def _trace_boundary(
    labels: np.ndarray,
    label: int,
    start: tuple[int, int],
    stride: int,
    perimeter: int,
) -> list[tuple[int, int]]:
    def matches(x: int, y: int) -> bool:
        return 0 <= x < labels.shape[1] and 0 <= y < labels.shape[0] and labels[y, x] == label

    def outgoing(vertex: tuple[int, int]) -> list[tuple[int, tuple[int, int]]]:
        x, y = vertex
        edges = []
        if matches(x, y) and not matches(x, y - 1):
            edges.append((0, (x + 1, y)))
        if matches(x - 1, y) and not matches(x, y):
            edges.append((1, (x, y + 1)))
        if matches(x - 1, y - 1) and not matches(x - 1, y):
            edges.append((2, (x - 1, y)))
        if matches(x, y - 1) and not matches(x - 1, y - 1):
            edges.append((3, (x, y - 1)))
        return edges

    def walk() -> list[tuple[int, int]]:
        current, previous = start, None
        sampled: list[tuple[int, int]] = []
        for steps in range(perimeter + 1):
            if steps % stride == 0:
                sampled.append(current)
            options = outgoing(current)
            if not options:
                break
            if previous is None:
                following = min(options, key=lambda edge: edge[0])[1]
            else:
                incoming = (current[0] - previous[0], current[1] - previous[1])
                following = min(
                    options,
                    key=lambda edge: _turn_priority(
                        incoming, (edge[1][0] - current[0], edge[1][1] - current[1])
                    ),
                )[1]
            previous, current = current, following
            if current == start:
                break
        return sampled

    points = walk()
    if not points:
        return [start, start]
    if points[-1] != points[0]:
        points.append(points[0])
    return points


def _turn_priority(incoming: tuple[int, int], outgoing: tuple[int, int]) -> int:
    cross = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
    if cross > 0:
        return 0
    if cross == 0 and incoming == outgoing:
        return 1
    if cross < 0:
        return 2
    return 3


def _douglas_peucker(
    points: list[tuple[int, int]], tolerance: float
) -> list[tuple[int, int]]:
    if len(points) <= 2:
        return points[:]
    kept = {0, len(points) - 1}
    pending = [(0, len(points) - 1)]
    while pending:
        first_index, last_index = pending.pop()
        start, end = points[first_index], points[last_index]
        dx, dy = end[0] - start[0], end[1] - start[1]
        length_squared = dx * dx + dy * dy
        farthest_distance = -1.0
        farthest_index = first_index
        for index in range(first_index + 1, last_index):
            point = points[index]
            if length_squared == 0:
                distance = hypot(point[0] - start[0], point[1] - start[1])
            else:
                cross = abs(
                    dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0]
                )
                distance = cross / length_squared**0.5
            if distance > farthest_distance:
                farthest_distance, farthest_index = distance, index
        if farthest_distance > tolerance:
            kept.add(farthest_index)
            pending.append((first_index, farthest_index))
            pending.append((farthest_index, last_index))
    return [points[index] for index in sorted(kept)]
