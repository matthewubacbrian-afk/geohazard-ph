from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.services.scene_analysis import (
    InvalidSceneImage,
    PanopticSegment,
    PanopticSegmenter,
    analyze_scene,
    decode_scene_image,
)


def jpeg_bytes(size: tuple[int, int] = (10, 10), *, exif_orientation: int | None = None) -> bytes:
    image = Image.new("RGB", size, "red")
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[274] = exif_orientation
        image.info["exif"] = exif.tobytes()
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=image.info.get("exif", b""))
    return buffer.getvalue()


def segment(class_name: str, mask: np.ndarray, confidence: float = 0.9) -> PanopticSegment:
    return PanopticSegment(class_name, mask, confidence)


class FakeSegmenter:
    def __init__(self, segments: list[PanopticSegment]) -> None:
        self.segments = segments

    def segment(self, image: Image.Image) -> list[PanopticSegment]:
        return self.segments


def analyze(image: Image.Image, segments: list[PanopticSegment]):
    segmenter: PanopticSegmenter = FakeSegmenter(segments)
    return analyze_scene(image, segmenter)


def test_decode_requires_jpeg_content_type_and_signature() -> None:
    data = jpeg_bytes()
    with pytest.raises(InvalidSceneImage):
        decode_scene_image(data, "image/png")
    with pytest.raises(InvalidSceneImage):
        decode_scene_image(b"not a jpeg", "image/jpeg")


@pytest.mark.parametrize(
    "size",
    [(4097, 1), (4000, 3001)],
)
def test_decode_rejects_oversized_dimensions(size: tuple[int, int]) -> None:
    with pytest.raises(InvalidSceneImage):
        decode_scene_image(jpeg_bytes(size), "image/jpeg")


def test_decode_rejects_malformed_and_truncated_jpeg() -> None:
    with pytest.raises(InvalidSceneImage):
        decode_scene_image(b"\xff\xd8\xffbroken", "image/jpeg")
    with pytest.raises(InvalidSceneImage):
        decode_scene_image(jpeg_bytes()[:-4], "image/jpeg")


def test_decode_normalizes_orientation_to_rgb_and_drops_metadata() -> None:
    decoded = decode_scene_image(jpeg_bytes((3, 2), exif_orientation=6), "image/jpeg")
    assert decoded.mode == "RGB"
    assert decoded.size == (2, 3)
    assert not decoded.getexif()


def test_analyze_filters_labels_confidence_and_small_components() -> None:
    base = np.zeros((20, 20), dtype=bool)
    base[:3, :3] = True
    tiny = np.zeros_like(base)
    tiny[18, 18] = True
    result = analyze(
        Image.new("RGB", (20, 20)),
        [
            segment("road", base),
            segment("floor", base),
            segment("grass", base, 0.49),
            segment("gravel", tiny),
        ],
    )
    assert result.result_status == "candidates_found"
    assert [candidate.surface_class for candidate in result.candidate_regions] == ["road"]


def test_analyze_splits_four_connected_components_and_returns_closed_normalized_polygons() -> None:
    mask = np.zeros((10, 10), dtype=bool)
    mask[:2, :2] = True
    mask[5:8, 5:8] = True
    result = analyze(Image.new("RGB", (10, 10)), [segment("pavement", mask)])
    assert len(result.candidate_regions) == 2
    candidate = result.candidate_regions[0]
    assert candidate.rank == 1
    assert candidate.polygon[0] == candidate.polygon[-1]
    assert len(candidate.polygon) <= 64
    assert all(0 <= point.x <= 1 and 0 <= point.y <= 1 for point in candidate.polygon)
    assert candidate.area_fraction == pytest.approx(0.09)
    assert candidate.compactness == pytest.approx(4 * np.pi * 9 / 12**2)


def test_analyze_ranks_candidates_with_spec_formula_and_tie_breaks_by_area() -> None:
    image = Image.new("RGB", (10, 10))
    large = np.zeros((10, 10), dtype=bool)
    large[:3, :3] = True
    small = np.zeros_like(large)
    small[5:7, 5:7] = True
    result = analyze(image, [segment("road", large, 0.8), segment("grass", small, 0.9)])
    by_class = {candidate.surface_class: candidate for candidate in result.candidate_regions}
    road = by_class["road"]
    road_expected = 0.5 + min(4 * np.pi * 9 / 12**2, 1) * 0.3 + 0.8 * 0.2
    assert road.ranking_score == pytest.approx(road_expected, abs=1e-6)
    grass = by_class["grass"]
    grass_expected = (4 / 9) * 0.5 + min(4 * np.pi * 4 / 8**2, 1) * 0.3 + 0.9 * 0.2
    assert grass.ranking_score == pytest.approx(grass_expected, abs=1e-6)


def test_analyze_breaks_equal_score_and_area_ties_by_top_left_position() -> None:
    left = np.zeros((10, 10), dtype=bool)
    left[1:3, 1:3] = True
    right = np.zeros_like(left)
    right[6:8, 6:8] = True
    result = analyze(
        Image.new("RGB", (10, 10)),
        [segment("road", right), segment("grass", left)],
    )
    assert [candidate.surface_class for candidate in result.candidate_regions] == ["grass", "road"]


def test_analyze_limits_candidates_to_five_and_deduplicates_cues() -> None:
    image = Image.new("RGB", (20, 20))
    segments = []
    for index, name in enumerate(("road", "pavement", "grass", "gravel", "floor-wood", "ground-other")):
        mask = np.zeros((20, 20), dtype=bool)
        mask[index * 3 : index * 3 + 3, :3] = True
        segments.append(segment(name, mask, 0.6 + index / 10))
    segments.extend([segment("grass", np.zeros((20, 20), bool), 0.75)])
    result = analyze(image, segments)
    assert len(result.candidate_regions) == 5
    assert [cue.class_name for cue in result.visual_cues] == sorted(cue.class_name for cue in result.visual_cues)
    assert next(cue.model_confidence for cue in result.visual_cues if cue.class_name == "grass") == 0.8


def test_analyze_returns_no_candidate_when_all_components_are_too_small() -> None:
    mask = np.zeros((20, 20), dtype=bool)
    mask[0, 0] = True
    result = analyze(Image.new("RGB", (20, 20)), [segment("grass", mask)])
    assert result.result_status == "no_clear_candidate"
    assert result.candidate_regions == ()


def test_analyze_ignores_non_finite_model_confidence() -> None:
    mask = np.ones((10, 10), dtype=bool)
    result = analyze(Image.new("RGB", (10, 10)), [segment("road", mask, float("nan"))])
    assert result.result_status == "no_clear_candidate"
