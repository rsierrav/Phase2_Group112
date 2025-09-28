# src/metrics/performance_claims.py

from typing import Any, Dict, List
import time
import re
from .protocol import Metric


class PerformanceClaims(Metric):
    """
    Metric to evaluate the evidence of good performance for a given model.
    Uses multiple sources in the parsed data to calculate a score, with
    fallback logic if some fields are missing.
    """

    def __init__(self) -> None:
        self.score: float = 0.0
        self.latency: float = 0.0

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant performance-related data from parsed metadata.
        """
        metadata = parsed_data.get("metadata", {})

        return {
            "model_index": metadata.get("model-index", []),
            "tags": metadata.get("tags", []),
            "cardData": metadata.get("cardData", {}),
            "downloads": metadata.get("downloads", 0),
            "likes": metadata.get("likes", 0),
            "description": metadata.get("description", ""),
            "widgetData": metadata.get("widgetData", []),
            "transformersInfo": metadata.get("transformersInfo", {}),
            "category": parsed_data.get("category", "UNKNOWN"),
        }

    def calculate_score(self, data: Dict[str, Any]) -> None:
        """
        Calculate performance claims score based on multiple evidence sources.
        Uses fallback alternatives if primary sources are missing.
        """
        if data.get("category", "UNKNOWN") != "MODEL":
            self.score = 0.0
            return

        total_score = 0.0

        # --------------------------
        # Benchmark evidence
        # --------------------------
        benchmark_score = 0.0
        benchmark_evidence: List[str] = []

        # 1. model_index.results
        model_index = data.get("model_index", [])
        if model_index and isinstance(model_index, list):
            for entry in model_index:
                if isinstance(entry, dict) and entry.get("results"):
                    benchmark_score += 0.4
                    benchmark_evidence.append(f"{len(entry['results'])} benchmark results")
                    if len(entry["results"]) > 1:
                        benchmark_score += 0.1
                    break

        # 2. cardData.metrics fallback
        if benchmark_score == 0.0:
            card_data = data.get("cardData", {})
            if isinstance(card_data, dict) and card_data.get("metrics"):
                benchmark_score += 0.3
                benchmark_evidence.append(f"cardData metrics found: {len(card_data['metrics'])}")

        # 3. description fallback
        if benchmark_score == 0.0:
            description = data.get("description", "")
            if description and re.search(r"benchmark|leaderboard|state-of-the-art|SOTA", description, re.IGNORECASE):
                benchmark_score += 0.2
                benchmark_evidence.append("description mentions benchmark/SOTA")

        total_score += benchmark_score

        # --------------------------
        # Performance tags
        # --------------------------
        tags_score = 0.0
        tags_evidence: List[str] = []

        tags = data.get("tags", [])
        performance_tags = [
            "arxiv:",
            "leaderboard",
            "benchmark",
            "evaluation",
            "sota",
            "state-of-the-art",
            "performance",
        ]

        # 1. tags
        matched_tags = [t for t in tags if isinstance(t, str) and any(pt in t.lower() for pt in performance_tags)]
        if matched_tags:
            tags_score += 0.2
            tags_evidence.extend(matched_tags)

        # 2. description fallback
        if tags_score == 0.0:
            description = data.get("description", "")
            if description:
                matches = re.findall(r"arxiv:\d{4}\.\d{4,5}|SOTA|state-of-the-art", description, re.IGNORECASE)
                if matches:
                    tags_score += 0.2
                    tags_evidence.extend(matches)

        # 3. widgetData / transformersInfo fallback
        if tags_score == 0.0:
            widget_data = data.get("widgetData", [])
            transformers_info = data.get("transformersInfo", {})
            if any("benchmark" in str(wd).lower() for wd in widget_data):
                tags_score += 0.1
                tags_evidence.append("benchmark found in widgetData")
            elif any("evaluation" in str(v).lower() for v in transformers_info.values()):
                tags_score += 0.1
                tags_evidence.append("evaluation info found in transformersInfo")

        total_score += tags_score

        community_score = 0.0
        downloads = data.get("downloads", 0)
        likes = data.get("likes", 0)
        transformers_info = data.get("transformersInfo", {})
        card_data = data.get("cardData", {})

        if downloads > 1000 or likes > 10:
            community_score += 0.1
        elif downloads > 100 or likes > 5:
            community_score += 0.05

        # 2. followers fallback
        followers = transformers_info.get("followers", 0)
        if community_score == 0.0 and followers > 500:
            community_score += 0.05

        # 3. ratings fallback
        ratings = card_data.get("ratings", [])
        if community_score == 0.0 and ratings:
            community_score += 0.05

        total_score += community_score

        # Cap at 1.0
        self.score = min(total_score, 1.0)

    def process_score(self, parsed_data: Dict[str, Any]) -> None:
        """
        Process parsed data and calculate performance score.
        Measures processing latency.
        """
        start_time = time.perf_counter()
        try:
            data = self.get_data(parsed_data)
            self.calculate_score(data)
        except Exception as e:
            self.score = 0.0
            print(f"[PerformanceClaims] Error calculating score: {e}")
        end_time = time.perf_counter()
        self.latency = (end_time - start_time) * 1000.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
