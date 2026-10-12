"""Lazy, cache-only adapter for the pinned panoptic model."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from app.services.scene_analysis import PanopticSegment, SceneAnalysisUnavailable


class LocalPanopticSegmenter:
    def __init__(self, model_id: str, revision: str, cache_dir: Path):
        self.model_id = model_id
        self.revision = revision
        self.cache_dir = cache_dir
        self._processor = None
        self._model = None

    def _load(self) -> None:
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
            self._processor = AutoImageProcessor.from_pretrained(
                self.model_id,
                revision=self.revision,
                cache_dir=self.cache_dir,
                local_files_only=True,
            )
            self._model = DetrForSegmentation.from_pretrained(
                self.model_id,
                revision=self.revision,
                cache_dir=self.cache_dir,
                local_files_only=True,
                config=config,
            )
            self._model.eval()
        except Exception as exc:
            raise SceneAnalysisUnavailable("Pinned scene model is unavailable") from exc

    def segment(self, image: Image.Image) -> list[PanopticSegment]:
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
