import unittest
from src.metrics.performance_claims import PerformanceClaims


class TestPerformanceClaims(unittest.TestCase):
    def setUp(self):
        self.metric = PerformanceClaims()

    def test_initialization(self):
        self.assertEqual(self.metric.get_score(), 0.0)
        self.assertEqual(self.metric.get_latency(), 0.0)

    def test_non_model_category(self):
        data = {"category": "DATASET", "metadata": {}}
        self.metric.process_score(data)
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_model_index_with_results(self):
        data = {
            "category": "MODEL",
            "metadata": {"model-index": [{"results": [{"task": "classification"}]}]},
        }
        self.metric.process_score(data)
        self.assertAlmostEqual(self.metric.get_score(), 0.4)

    def test_model_index_with_multiple_results(self):
        data = {
            "category": "MODEL",
            "metadata": {"model-index": [{"results": [{"task": "a"}, {"task": "b"}]}]},
        }
        self.metric.process_score(data)
        self.assertAlmostEqual(self.metric.get_score(), 0.5)

    def test_performance_tags(self):
        data = {"category": "MODEL", "metadata": {"tags": ["benchmark"]}}
        self.metric.process_score(data)
        self.assertEqual(self.metric.get_score(), 0.2)

    def test_carddata_metrics(self):
        # Fixed: Your code looks for cardData.metrics, not cardData.model-index
        data = {
            "category": "MODEL",
            "metadata": {
                "model-index": [],  # Empty so it falls back to cardData
                "cardData": {"metrics": [{"metric1": "value1"}]},
            },
        }
        self.metric.process_score(data)
        self.assertAlmostEqual(self.metric.get_score(), 0.3)

    def test_downloads_and_likes_thresholds(self):
        # Fixed expectations to match actual community scoring logic
        cases = [
            (50, 2, 0.0),  # Below both thresholds
            (200, 2, 0.05),  # downloads > 100, likes < 5
            (50, 6, 0.05),  # downloads < 100, likes > 5
            (2000, 0, 0.1),  # downloads > 1000
            (0, 20, 0.1),  # likes > 10
            (2000, 20, 0.1),  # Both high (doesn't double-count)
        ]
        for downloads, likes, expected in cases:
            with self.subTest(downloads=downloads, likes=likes, expected=expected):
                data = {
                    "category": "MODEL",
                    "metadata": {"downloads": downloads, "likes": likes},
                }
                self.metric.process_score(data)
                self.assertAlmostEqual(self.metric.get_score(), expected, places=2)

    def test_combined_high_score(self):
        """Test combination of multiple evidence sources"""
        data = {
            "category": "MODEL",
            "metadata": {
                "model-index": [{"results": [{"task": "a"}, {"task": "b"}]}],  # 0.5
                "tags": ["benchmark"],  # 0.2
                "downloads": 2000,  # 0.1
                "likes": 20,  # (doesn't add more, same threshold)
            },
        }
        self.metric.process_score(data)
        # 0.5 (benchmark) + 0.2 (tags) + 0.1 (community) = 0.8
        self.assertAlmostEqual(self.metric.get_score(), 0.8, places=2)

    def test_process_score_sets_latency(self):
        parsed = {
            "category": "MODEL",
            "metadata": {"tags": ["benchmark"], "downloads": 2000, "likes": 50},
        }
        self.metric.process_score(parsed)
        self.assertGreater(self.metric.get_latency(), 0.0)
        self.assertGreaterEqual(self.metric.get_score(), 0.0)

    def test_arxiv_tags(self):
        """Test that arxiv tags are recognized"""
        data = {
            "category": "MODEL",
            "metadata": {"tags": ["arxiv:2020.12345"]},
        }
        self.metric.process_score(data)
        self.assertEqual(self.metric.get_score(), 0.2)

    def test_description_fallback(self):
        """Test description parsing for benchmark mentions"""
        data = {
            "category": "MODEL",
            "metadata": {
                "description": "This model achieves state-of-the-art performance on benchmark datasets.",
                "tags": [],  # No performance tags
                "model-index": [],  # No model index
            },
        }
        self.metric.process_score(data)
        # Description contains both "benchmark" (0.2) and "state-of-the-art" (0.2) = 0.4
        self.assertEqual(self.metric.get_score(), 0.4)

    def test_description_benchmark_only(self):
        """Test description parsing for benchmark mentions only"""
        data = {
            "category": "MODEL",
            "metadata": {
                "description": "This model was evaluated on standard benchmark datasets.",
                "tags": [],  # No performance tags
                "model-index": [],  # No model index
            },
        }
        self.metric.process_score(data)
        self.assertEqual(self.metric.get_score(), 0.2)  # Only benchmark fallback


if __name__ == "__main__":
    unittest.main()
