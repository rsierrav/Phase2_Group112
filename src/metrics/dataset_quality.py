# src/metrics/dataset_quality.py

import os
import time
import requests
from typing import Any, Dict
from .protocol import Metric


class DatasetQualityMetric(Metric):
    """
    Metric to evaluate dataset documentation and example code clarity
    using Purdue GenAI Studio (LLM).
    """

    def __init__(self) -> None:
        self.score: float = -1.0
        self.latency: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract dataset URL and code URL for scoring.
        """
        return {
            "dataset_url": parsed_data.get("dataset_url", ""),
            "code_url": parsed_data.get("code_url", ""),
        }

    def calculate_score(self, data: Dict[str, str]) -> None:
        """
        Call Purdue GenAI Studio to evaluate dataset/code clarity.
        Updates self.score with a float between 0.0 and 1.0.
        """
        api_key = os.getenv("GEN_AI_STUDIO_API_KEY")
        if not api_key:
            # Spec says unimplemented metrics should default to -1
            self.score = -1.0
            self.latency = -1.0
            return

        dataset_url = data.get("dataset_url", "")
        code_url = data.get("code_url", "")

        prompt = f"""
        You are a Software Engineer, working for a company evaluating models.
        You are trying to determine whether a model’s dataset and example code
        are sufficiently documented and useful.

        Dataset link: {dataset_url or "N/A"}
        Example code link: {code_url or "N/A"}

        Criteria:
        - Is the dataset clearly described (purpose, size, usage)?
        - Is there enough code (in repo/examples) to get started?
        - Would a new engineer quickly re-use this resource?

        Answer with only a numeric score between 0.0 (poor) and 1.0 (excellent).
        """

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "llama4:latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }

        start = time.time()
        try:
            resp = requests.post(
                "https://genai.api.purdue.edu/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            score = float(content)
            self.score = max(0.0, min(1.0, score))
        except Exception:
            self.score = -1.0  # fallback if API call fails
        finally:
            self.latency = int((time.time() - start) * 1000)  # ms

    def get_example_count(self, parsed_data: Dict[str, Any]) -> int:
        """Get number of examples/samples in dataset"""
        if parsed_data.get("category") == "DATASET":
            card_data = parsed_data.get("cardData", {})
            dataset_info = card_data.get("dataset_info", {})

            if isinstance(dataset_info, dict):
                splits = dataset_info.get("splits", [])
                total_examples = 0
                for split in splits:
                    if isinstance(split, dict):
                        total_examples += split.get("num_examples", 0)
                return total_examples
            elif isinstance(dataset_info, list) and dataset_info:
                total_examples = 0
                for info in dataset_info:
                    splits = info.get("splits", [])
                    for split in splits:
                        if isinstance(split, dict):
                            total_examples += split.get("num_examples", 0)
                return total_examples
        return 0

    def get_description(self, parsed_data: Dict[str, Any]) -> str:
        return parsed_data.get("description", "")

    def get_metadata_completeness(self, parsed_data: Dict[str, Any]) -> float:
        card_data = parsed_data.get("cardData", {})

        metadata_fields = [
            "task_categories",
            "language",
            "size_categories",
            "source_datasets",
            "annotations_creators",
            "language_creators",
        ]

        present_fields = 0
        for field in metadata_fields:
            if field in card_data and card_data[field]:
                value = card_data[field]
                if isinstance(value, list) and len(value) > 0:
                    present_fields += 1
                elif isinstance(value, str) and value.strip():
                    present_fields += 1

        return present_fields / len(metadata_fields)

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
