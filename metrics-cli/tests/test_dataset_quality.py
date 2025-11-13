import unittest
import os
from unittest.mock import patch
from src.metrics.dataset_quality import DatasetQualityMetric


class TestDatasetQualityMetric(unittest.TestCase):
    def setUp(self):
        self.metric = DatasetQualityMetric()

    def test_initialization(self):
        self.assertEqual(self.metric.get_score(), -1.0)
        self.assertEqual(self.metric.get_latency(), -1.0)

    def test_calculate_score_with_zero_examples(self):
        data = {"example_count": 0}
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_heuristic_score_with_long_description(self):
        data = {"description": "word " * 200}
        self.assertEqual(self.metric._calculate_heuristic_score(data), 0.2)

    def test_heuristic_score_with_medium_description(self):
        data = {"description": "word " * 60}
        self.assertEqual(self.metric._calculate_heuristic_score(data), 0.2)

    def test_heuristic_score_with_readme_sibling(self):
        data = {"siblings": [{"rfilename": "README.md"}]}
        self.assertEqual(self.metric._calculate_heuristic_score(data), 0.1)

    def test_heuristic_score_with_example_file(self):
        data = {"siblings": [{"rfilename": "tutorial.ipynb"}]}
        self.assertEqual(self.metric._calculate_heuristic_score(data), 0.1)

    @patch("src.metrics.dataset_quality.requests.post")
    def test_calculate_score_with_api_key_and_request_failure(self, mock_post):
        os.environ["GEN_AI_STUDIO_API_KEY"] = "dummy"
        mock_post.side_effect = Exception("network fail")
        data = {"description": "A dataset description"}
        self.metric.calculate_score(data)
        # should fallback to heuristic
        self.assertGreaterEqual(self.metric.get_score(), 0.0)
        del os.environ["GEN_AI_STUDIO_API_KEY"]

    def test_calculate_score_with_nonzero_examples(self):
        data = {"example_count": 500}
        self.metric.calculate_score(data)
        # Accept non-negative score (future logic may increase this)
        self.assertGreaterEqual(self.metric.get_score(), 0.0)

    def test_calculate_score_with_missing_data(self):
        data = {}
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.0)

    def test_process_score_sets_latency_and_score(self):
        parsed = {"description": "This dataset has some documentation"}
        self.metric.process_score(parsed)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)
        self.assertGreaterEqual(self.metric.get_score(), 0.0)


if __name__ == "__main__":
    unittest.main()
