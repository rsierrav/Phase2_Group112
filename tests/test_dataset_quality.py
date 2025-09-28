import unittest
from src.metrics.dataset_quality import DatasetQualityMetric


class TestDatasetQualityMetric(unittest.TestCase):
    def setUp(self):
        self.metric = DatasetQualityMetric()

    def test_initialization(self):
        self.assertEqual(self.metric.get_score(), -1.0)
        self.assertEqual(self.metric.get_latency(), -1.0)

    def test_calculate_score_with_example_count(self):
        data = {"example_count": 5000}
        self.metric.calculate_score(data)
        # Updated: implementation no longer uses example_count
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_calculate_score_with_small_example_count(self):
        data = {"example_count": 50}
        self.metric.calculate_score(data)
        # Updated: implementation no longer uses example_count
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_calculate_score_with_zero_examples(self):
        data = {"example_count": 0}
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_calculate_score_with_missing_examples(self):
        data = {}
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_calculate_score_with_dataset_url_only(self):
        data = {"dataset_url": "https://huggingface.co/datasets/foo/bar"}
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.3)

    def test_calculate_score_with_code_url_only(self):
        data = {"code_url": "https://github.com/foo/bar"}
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.3)

    def test_calculate_score_with_both_urls(self):
        data = {
            "dataset_url": "https://huggingface.co/datasets/foo/bar",
            "code_url": "https://github.com/foo/bar",
        }
        self.metric.calculate_score(data)
        # 0.3 + 0.3 = 0.6 (fallback heuristic)
        self.assertEqual(self.metric.get_score(), 0.6)

    def test_process_score_sets_latency(self):
        parsed = {
            "category": "MODEL",
            "dataset_url": "https://huggingface.co/datasets/foo/bar",
            "code_url": "https://github.com/foo/bar",
        }
        self.metric.process_score(parsed)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)
        self.assertGreaterEqual(self.metric.get_score(), 0.0)


if __name__ == "__main__":
    unittest.main()
