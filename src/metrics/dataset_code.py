# src/metrics/dataset_code.py

import os
import requests
from typing import Any, Dict
from .protocol import Metric


class DatasetCodeMetric(Metric):
    """
    Metric to evaluate whether a model's dataset and example code
    are well documented.
    """

    def __init__(self):
        self.score: float = 0.0
        self.latency: float = 0.0
        self.weight: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract dataset documentation and example code from the parser output.
        """
        return {
            "dataset_doc": parsed_data.get("dataset_doc", ""),
            "example_code": parsed_data.get("example_code", ""),
        }

    def calculate_score(self, data: Dict[str, str]) -> None:
        """
        Call Purdue GenAI Studio to evaluate documentation clarity.
        Updates self.score with a float between 0.0 and 1.0.
        """
        api_key = os.getenv("GEN_AI_STUDIO_API_KEY")
        if not api_key:
            raise RuntimeError("GEN_AI_STUDIO_API_KEY not set in environment")

        dataset_doc = data.get("dataset_doc", "")
        example_code = data.get("example_code", "")

        prompt = f"""
        You are evaluating machine learning dataset and code documentation.

        Dataset documentation:
        {dataset_doc[:2000]}

        Example code:
        {example_code[:1000]}

        Criteria:
        - Is the dataset clearly described (purpose, size, usage)?
        - Is the example code sufficient to get started?
        - Would a new engineer quickly re-use this resource?

        Answer with only a numeric score between 0.0 (poor) and 1.0 (excellent).
        """

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # TA said we have to use purdue genai studio
        payload = {
            "model": "llama4:latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }

        resp = requests.post(
            "https://genai.api.purdue.edu/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()

        try:
            score = float(content)
            self.score = max(0.0, min(1.0, score))
        except ValueError:
            self.score = 0.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
