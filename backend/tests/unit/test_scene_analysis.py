import tracemalloc
from io import BytesIO

import numpy as np
import pytest
from PIL import Image, ImageFilter

from app.services.scene_analysis import (
    MIN_SHARPNESS_SCORE,
    InvalidSceneImage,
    PanopticSegment,
    PanopticSegmenter,
    SceneImageQualityWarning,
    analyze_scene,
    decode_scene_image,
    estimate_sharpness,
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
    return analyze_scene(image, segmenter, accept_quality_warning=True)


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


def test_blurred_image_is_flagged_by_sharpness_metric() -> None:
    image = Image.new("L", (64, 64), 0)
    for x in range(0, 64, 8):
        image.paste(255, (x, 0, x + 4, 64))
    sharp = estimate_sharpness(image)
    blurred = estimate_sharpness(image.filter(ImageFilter.GaussianBlur(radius=2)))
    assert sharp >= MIN_SHARPNESS_SCORE
    assert blurred < MIN_SHARPNESS_SCORE


def test_likely_blurry_image_warns_before_model_inference() -> None:
    image = Image.new("L", (64, 64), 127)

    class TrackingSegmenter:
        called = False

        def segment(self, image):
            self.called = True
            return []

    segmenter = TrackingSegmenter()
    with pytest.raises(SceneImageQualityWarning):
        analyze_scene(image, segmenter)
    assert not segmenter.called


def test_explicit_quality_override_allows_blurry_image_analysis() -> None:
    image = Image.new("L", (64, 64), 127)
    segmenter = FakeSegmenter([])
    result = analyze_scene(image, segmenter, accept_quality_warning=True)
    assert result.result_status == "no_clear_candidate"


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


def test_analyze_does_not_join_diagonally_touching_pixels() -> None:
    mask = np.zeros((2, 2), dtype=bool)
    mask[0, 0] = True
    mask[1, 1] = True
    result = analyze(Image.new("RGB", (2, 2)), [segment("grass", mask)])
    assert len(result.candidate_regions) == 2
    assert all(candidate.area_fraction == pytest.approx(0.25) for candidate in result.candidate_regions)


def test_concave_component_polygon_is_clockwise_and_has_four_distinct_vertices() -> None:
    mask = np.zeros((12, 12), dtype=bool)
    mask[1:9, 1:3] = True
    mask[7:9, 1:9] = True
    candidate = analyze(Image.new("RGB", (12, 12)), [segment("road", mask)]).candidate_regions[0]
    vertices = [(point.x, point.y) for point in candidate.polygon[:-1]]
    signed_area = sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(vertices, vertices[1:] + vertices[:1])
    ) / 2
    assert len(set(vertices)) >= 4
    assert signed_area > 0  # positive shoelace area is clockwise in image coordinates


def test_polygon_simplification_preserves_narrow_component_geometry() -> None:
    mask = np.zeros((12, 12), dtype=bool)
    mask[0, 4:6] = True
    mask[1, 4] = True
    mask[2:4, 4:6] = True
    mask[4, 5] = True
    mask[5, 5:7] = True
    mask[6, 5] = True
    candidate = analyze(Image.new("RGB", (12, 12)), [segment("road", mask)]).candidate_regions[0]
    vertices = [(point.x, point.y) for point in candidate.polygon[:-1]]
    signed_area = sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(vertices, vertices[1:] + vertices[:1])
    ) / 2
    assert len(set(vertices)) >= 4
    assert signed_area > 0


def test_dense_component_does_not_materialize_a_python_object_per_pixel() -> None:
    image = Image.new("RGB", (640, 640))
    mask = np.ones((640, 640), dtype=bool)
    tracemalloc.start()
    try:
        analyze(image, [segment("road", mask)])
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 12 * 1024 * 1024


def test_dense_near_pixel_cap_image_yields_candidate_without_per_pixel_objects() -> None:
    side = 3464  # 11,999,296 pixels, within the decoder's 12,000,000-pixel cap.
    image = Image.new("RGB", (side, side))
    mask = np.ones((side, side), dtype=bool)
    result = analyze(image, [segment("road", mask)])
    assert result.result_status == "candidates_found"
    assert result.candidate_regions[0].area_fraction == 1.0
    assert len(result.candidate_regions[0].polygon) <= 64


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
