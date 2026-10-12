"""Lazy, cache-only adapter for the pinned panoptic model."""

from __future__ import annotations

from pathlib import Path
from threading import RLock

import numpy as np
from PIL import Image

from app.services.scene_analysis import PanopticSegment, SceneAnalysisUnavailable

MODEL_ID = "facebook/detr-resnet-50-panoptic"
MODEL_REVISION = "d53b52a799403a8867920f82c869e40732b47037"


class LocalPanopticSegmenter:
    def __init__(self, cache_dir: Path):
        self.model_id = MODEL_ID
        self.revision = MODEL_REVISION
        self.cache_dir = cache_dir
        self._processor = None
        self._model = None
        self._model_lock = RLock()

    def _load(self) -> None:
        with self._model_lock:
            if self._model is not None:
                return
            try:
                from transformers import AutoImageProcessor, DetrConfig, DetrForSegmentation

                config = DetrConfig.from_pretrained(
                    self.model_id,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                    local_files_only=True,
                )
                config.use_pretrained_backbone = False
                processor = AutoImageProcessor.from_pretrained(
                    self.model_id,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                    local_files_only=True,
                )
                model = DetrForSegmentation.from_pretrained(
                    self.model_id,
                    revision=self.revision,
                    cache_dir=self.cache_dir,
                    local_files_only=True,
                    config=config,
                )
                model.eval()
                self._processor = processor
                self._model = model
            except Exception as exc:
                raise SceneAnalysisUnavailable("Pinned scene model is unavailable") from exc

    def segment(self, image: Image.Image) -> list[PanopticSegment]:
        with self._model_lock:
            self._load()
            try:
                import torch

                with torch.inference_mode():
                    inputs = self._processor(images=image, return_tensors="pt")
                    output = self._model(**inputs)
                    parsed = self._processor.post_process_panoptic_segmentation(
                        output,
                        target_sizes=[(image.height, image.width)],
                    )[0]
                labels = self._model.config.id2label
                segments = []
                for info in parsed["segments_info"]:
                    label = labels.get(info["label_id"], "")
                    mask = parsed["segmentation"].cpu().numpy() == info["id"]
                    segments.append(PanopticSegment(label, np.asarray(mask, dtype=bool), float(info["score"])))
                return segments
            except SceneAnalysisUnavailable:
                raise
            except Exception as exc:
                raise SceneAnalysisUnavailable("Pinned scene model is unavailable") from exc
