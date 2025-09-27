# src/metrics/performance_claims.py
import time
import requests
import re
from typing import Dict, Any, List
from .protocol import Metric


class PerformanceClaims(Metric):
    """
    Evaluate the quality and verifiability of performance claims
    made about a model based on documentation and model cards.
    """

    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0

    def _extract_metrics_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract performance metrics from text."""
        metrics = []

        # Common ML metrics patterns
        metric_patterns = [
            r"accuracy[:\s]*(\d+\.?\d*)%?",
            r"f1[:\s]*(\d+\.?\d*)",
            r"bleu[:\s]*(\d+\.?\d*)",
            r"rouge[:\s]*(\d+\.?\d*)",
            r"wer[:\s]*(\d+\.?\d*)%?",
            r"loss[:\s]*(\d+\.?\d*)",
            r"perplexity[:\s]*(\d+\.?\d*)",
            r"auc[:\s]*(\d+\.?\d*)",
            r"precision[:\s]*(\d+\.?\d*)%?",
            r"recall[:\s]*(\d+\.?\d*)%?",
            r"map[:\s]*(\d+\.?\d*)",
            r"top-?1[:\s]*(\d+\.?\d*)%?",
            r"top-?5[:\s]*(\d+\.?\d*)%?",
        ]

        text_lower = text.lower()
        for pattern in metric_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                metric_name = pattern.split("[")[0]
                value = float(match.group(1))
                metrics.append(
                    {
                        "name": metric_name,
                        "value": value,
                        "context": text[max(0, match.start() - 50) : match.end() + 50],
                    }
                )

        return metrics

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance claims from model metadata."""
        metadata = parsed_data.get("metadata", {})

        # Initialize data structure
        data = {
            "has_model_card": False,
            "has_benchmarks": False,
            "has_metrics": False,
            "metrics_count": 0,
            "has_datasets_tested": False,
            "has_comparisons": False,
            "documentation_quality": 0.0,
        }

        # Check for HuggingFace model-index (structured performance data)
        model_index = metadata.get("model-index", [])
        if model_index:
            data["has_benchmarks"] = True
            data["has_metrics"] = True
            data["has_datasets_tested"] = True

            # Count metrics
            total_metrics = 0
            for model_entry in model_index:
                results = model_entry.get("results", [])
                for result in results:
                    metrics = result.get("metrics", [])
                    total_metrics += len(metrics)

            data["metrics_count"] = total_metrics

        # Check card data for performance information
        card_data = metadata.get("cardData", {})
        if card_data:
            data["has_model_card"] = True

        # Get README content for analysis
        readme_content = ""
        try:
            if "huggingface.co" in parsed_data.get("url", ""):
                if "/datasets/" in parsed_data.get("url", ""):
                    model_id = "datasets/" + "/".join(
                        parsed_data.get("url", "")
                        .split("huggingface.co/datasets/")[-1]
                        .split("/")[:2]
                    )
                else:
                    model_id = "/".join(
                        parsed_data.get("url", "").split("huggingface.co/")[-1].split("/")[:2]
                    )

                resp = requests.get(
                    f"https://huggingface.co/{model_id}/raw/main/README.md", timeout=10
                )
                if resp.status_code == 200:
                    readme_content = resp.text
        except Exception:
            pass

        # Analyze README for performance claims
        if readme_content:
            readme_lower = readme_content.lower()

            # Look for benchmark mentions
            benchmark_indicators = [
                "benchmark",
                "evaluation",
                "performance",
                "results",
                "accuracy",
                "f1",
                "bleu",
                "rouge",
                "wer",
            ]
            data["has_benchmarks"] = any(
                indicator in readme_lower for indicator in benchmark_indicators
            )

            # Look for dataset mentions
            dataset_indicators = [
                "dataset",
                "trained on",
                "evaluated on",
                "tested on",
                "glue",
                "squad",
                "coco",
                "imagenet",
                "librispeech",
            ]
            data["has_datasets_tested"] = any(
                indicator in readme_lower for indicator in dataset_indicators
            )

            # Look for comparisons
            comparison_indicators = [
                "compared to",
                "vs",
                "versus",
                "outperforms",
                "beats",
                "state-of-the-art",
                "sota",
                "baseline",
            ]
            data["has_comparisons"] = any(
                indicator in readme_lower for indicator in comparison_indicators
            )

            # Extract metrics from README
            extracted_metrics = self._extract_metrics_from_text(readme_content)
            if extracted_metrics:
                data["has_metrics"] = True
                data["metrics_count"] += len(extracted_metrics)

        return data

    def calculate_score(self, data: Dict[str, Any]) -> None:
        """Calculate performance claims score."""
        start = time.perf_counter()

        score = 0.0

        # Has model card (0-0.2)
        if data.get("has_model_card", False):
            score += 0.2

        # Has benchmarks (0-0.25)
        if data.get("has_benchmarks", False):
            score += 0.25

        # Has metrics with values (0-0.25)
        if data.get("has_metrics", False):
            metrics_count = data.get("metrics_count", 0)
            if metrics_count >= 5:
                score += 0.25
            elif metrics_count >= 3:
                score += 0.2
            elif metrics_count >= 1:
                score += 0.15
            else:
                score += 0.1

        # Tested on standard datasets (0-0.15)
        if data.get("has_datasets_tested", False):
            score += 0.15

        # Has comparisons to other models (0-0.15)
        if data.get("has_comparisons", False):
            score += 0.15

        self.score = min(1.0, score)

        end = time.perf_counter()
        self.latency = (end - start) * 1000.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
