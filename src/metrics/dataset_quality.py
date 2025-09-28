import os
import time
import requests
from typing import Any, Dict
from .protocol import Metric


class DatasetQualityMetric(Metric):
    """
    Metric to evaluate dataset documentation and example code clarity
    using Purdue GenAI Studio (LLM) with fallback to heuristic scoring.
    """

    def __init__(self) -> None:
        self.score: float = -1.0
        self.latency: float = -1.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract dataset URL, code URL, and metadata for scoring.
        """
        return {
            "dataset_url": parsed_data.get("dataset_url", ""),
            "code_url": parsed_data.get("code_url", ""),
            "description": parsed_data.get("description", ""),
            "cardData": parsed_data.get("cardData", {}),
            "siblings": parsed_data.get("siblings", []),
            "tags": parsed_data.get("tags", []),
        }

    def calculate_score(self, data: Dict[str, Any]) -> None:
        """
        Call Purdue GenAI Studio to evaluate dataset/code clarity.
        Falls back to heuristic scoring if API fails.
        """
        api_key = os.getenv("GEN_AI_STUDIO_API_KEY")
        start = time.time()

        dataset_url = data.get("dataset_url", "")
        code_url = data.get("code_url", "")

        # Try LLM API first if available
        if api_key:
            try:
                prompt = f"""
You are a Software Engineer evaluating model resources.
Dataset link: {dataset_url or "N/A"}
Code link: {code_url or "N/A"}

Rate the quality from 0.0 to 1.0 based on:
- Dataset clarity and documentation
- Code examples and usability
- Overall usefulness for developers

Respond with only a number between 0.0 and 1.0.
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

                resp = requests.post(
                    "https://genai.api.purdue.edu/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    score = float(content)
                    self.score = max(0.0, min(1.0, score))
                    self.latency = int((time.time() - start) * 1000)
                    return
            except Exception:
                pass  # Fall through to heuristic

        # Fallback to heuristic scoring
        self.score = self._calculate_heuristic_score(data)
        self.latency = int((time.time() - start) * 1000)

    def _calculate_heuristic_score(self, data: Dict[str, Any]) -> float:
        """
        Heuristic scoring based on available metadata.
        """
        score = 0.0

        # Check if we have any dataset or code URLs
        dataset_url = data.get("dataset_url", "")
        code_url = data.get("code_url", "")

        if dataset_url:
            score += 0.3
        if code_url:
            score += 0.3

        # Check description quality
        description = data.get("description", "")
        if len(description) > 100:
            score += 0.2
        elif len(description) > 50:
            score += 0.1

        # Check for documentation files
        siblings = data.get("siblings", [])
        has_readme = any(s.get("rfilename", "").upper().startswith("README") for s in siblings if isinstance(s, dict))
        if has_readme:
            score += 0.1

        # Check for examples or tutorials
        has_examples = any(
            "example" in s.get("rfilename", "").lower() or "tutorial" in s.get("rfilename", "").lower() for s in siblings if isinstance(s, dict)
        )
        if has_examples:
            score += 0.1

        return min(score, 1.0)

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
