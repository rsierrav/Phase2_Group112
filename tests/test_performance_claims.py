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

    def test_carddata_model_index(self):
        data = {
            "category": "MODEL",
            "metadata": {
                "model_index": [],
                "cardData": {"model-index": [{"results": [{}]}]},
            },
        }
        self.metric.process_score(data)
        self.assertAlmostEqual(self.metric.get_score(), 0.3)

    def test_downloads_and_likes_thresholds(self):
        cases = [
            (50, 2, 0.0),
            (200, 2, 0.05),
            (50, 6, 0.05),
            (2000, 0, 0.1),
            (0, 20, 0.1),
        ]
        for downloads, likes, expected in cases:
            data = {
                "category": "MODEL",
                "metadata": {"downloads": downloads, "likes": likes},
            }
            self.metric.process_score(data)
            self.assertAlmostEqual(self.metric.get_score(), expected)

    def test_score_maxes_at_seven_tenths(self):
        """Implementation maxes out at ~0.7, not 1.0"""
        data = {
            "category": "MODEL",
            "metadata": {
                "model-index": [{"results": [{}]}],
                "tags": ["benchmark"],
                "cardData": {"model-index": [{"results": [{}]}]},
                "downloads": 10000,
                "likes": 500,
            },
        }
        self.metric.process_score(data)
        self.assertAlmostEqual(self.metric.get_score(), 0.7, places=6)

    def test_process_score_sets_latency(self):
        parsed = {
            "category": "MODEL",
            "metadata": {"tags": ["benchmark"], "downloads": 2000, "likes": 50},
        }
        self.metric.process_score(parsed)
        self.assertGreater(self.metric.get_latency(), 0.0)
        self.assertGreaterEqual(self.metric.get_score(), 0.0)


if __name__ == "__main__":
    unittest.main()
