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


def analyze_scene(image: Image.Image, segmenter: PanopticSegmenter) -> SceneAnalysisResult:
    """Extract and rank bounded surface components from injected panoptic masks."""
    segments = segmenter.segment(image)
    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive")
    image_area = width * height

    cue_confidences: dict[str, float] = {}
    components: list[tuple[str, np.ndarray, int, int, float, float]] = []
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
        for component in _connected_components(mask):
            pixel_area = len(component)
            if pixel_area / image_area < MIN_COMPONENT_FRACTION:
                continue
            perimeter = _perimeter(component)
            compactness = min(4 * pi * pixel_area / (perimeter * perimeter), 1.0)
            top = min(y for _, y in component)
            left = min(x for x, _ in component)
            components.append(
                (segment.class_name, component, pixel_area, perimeter, confidence, compactness)
            )

    largest_area = max((item[2] for item in components), default=1)
    ranked: list[tuple[float, int, int, int, str, tuple[ImagePoint, ...], float, float, float]] = []
    for class_name, component, pixel_area, _perimeter_value, confidence, compactness in components:
        area_fraction = pixel_area / image_area
        score = (
            min(pixel_area / largest_area, 1.0) * 0.50
            + compactness * 0.30
            + confidence * 0.20
        )
        left = min(x for x, _ in component)
        top = min(y for _, y in component)
        polygon = _normalized_polygon(component, width, height)
        ranked.append(
            (score, pixel_area, top, left, class_name, polygon, area_fraction, compactness, confidence)
        )

    ranked.sort(key=lambda item: (-item[0], -item[1], item[2], item[3], item[4]))
    candidates = tuple(
        CandidateRegion(
            rank=index,
            surface_class=item[4],
            polygon=item[5],
            area_fraction=item[6],
            compactness=item[7],
            model_confidence=item[8],
            ranking_score=item[0],
        )
        for index, item in enumerate(ranked[:MAX_CANDIDATES], start=1)
    )
    cues = tuple(VisualCue(name, cue_confidences[name]) for name in sorted(cue_confidences))
    return SceneAnalysisResult(
        result_status="candidates_found" if candidates else "no_clear_candidate",
        candidate_regions=candidates,
        visual_cues=cues,
    )


def _connected_components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    height, width = mask.shape
    visited = np.zeros(mask.shape, dtype=bool)
    result: list[list[tuple[int, int]]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            visited[y, x] = True
            pending = [(x, y)]
            component: list[tuple[int, int]] = []
            while pending:
                current_x, current_y = pending.pop()
                component.append((current_x, current_y))
                for neighbor_x, neighbor_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if (
                        0 <= neighbor_x < width
                        and 0 <= neighbor_y < height
                        and mask[neighbor_y, neighbor_x]
                        and not visited[neighbor_y, neighbor_x]
                    ):
                        visited[neighbor_y, neighbor_x] = True
                        pending.append((neighbor_x, neighbor_y))
            result.append(component)
    return result


def _perimeter(component: list[tuple[int, int]]) -> int:
    pixels = set(component)
    return sum(
        sum(
            neighbor not in pixels
            for neighbor in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))
        )
        for x, y in pixels
    )


def _normalized_polygon(
    component: list[tuple[int, int]], width: int, height: int
) -> tuple[ImagePoint, ...]:
    edges: dict[tuple[int, int], list[tuple[int, int]]] = {}
    pixels = set(component)
    for x, y in pixels:
        if (x, y - 1) not in pixels:
            edges.setdefault((x, y), []).append((x + 1, y))
        if (x + 1, y) not in pixels:
            edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
        if (x, y + 1) not in pixels:
            edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
        if (x - 1, y) not in pixels:
            edges.setdefault((x, y + 1), []).append((x, y))

    start = min(edges, key=lambda point: (point[1], point[0]))
    boundary = [start]
    current = start
    previous = None
    for _ in range(sum(map(len, edges.values())) + 1):
        options = edges.get(current, [])
        if not options:
            break
        if previous is None or len(options) == 1:
            following = options[0]
        else:
            incoming = (current[0] - previous[0], current[1] - previous[1])
            following = min(
                options,
                key=lambda point: _turn_priority(
                    incoming, (point[0] - current[0], point[1] - current[1])
                ),
            )
        edges[current].remove(following)
        previous, current = current, following
        boundary.append(current)
        if current == start:
            break

    tolerance = 1.0
    simplified = _douglas_peucker(boundary, tolerance)
    while len(simplified) > MAX_POLYGON_POINTS - 1:
        tolerance *= 1.5
        simplified = _douglas_peucker(boundary, tolerance)
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return tuple(ImagePoint(x / width, y / height) for x, y in simplified)


def _turn_priority(incoming: tuple[int, int], outgoing: tuple[int, int]) -> int:
    cross = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
    if cross < 0:
        return 0
    if cross == 0 and incoming == outgoing:
        return 1
    if cross > 0:
        return 2
    return 3


def _douglas_peucker(
    points: list[tuple[int, int]], tolerance: float
) -> list[tuple[int, int]]:
    if len(points) <= 2:
        return points[:]
    start, end = points[0], points[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    farthest_distance = -1.0
    farthest_index = 0
    for index, point in enumerate(points[1:-1], start=1):
        if length_squared == 0:
            distance = hypot(point[0] - start[0], point[1] - start[1])
        else:
            cross = abs(dy * point[0] - dx * point[1] + end[0] * start[1] - end[1] * start[0])
            distance = cross / length_squared**0.5
        if distance > farthest_distance:
            farthest_distance, farthest_index = distance, index
    if farthest_distance <= tolerance:
        return [start, end]
    left = _douglas_peucker(points[: farthest_index + 1], tolerance)
    right = _douglas_peucker(points[farthest_index:], tolerance)
    return left[:-1] + right
