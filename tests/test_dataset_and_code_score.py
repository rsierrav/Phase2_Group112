import unittest

from src.metrics.dataset_and_code import DatasetAndCodeMetric


class TestDatasetAndCodeMetric(unittest.TestCase):

    def setUp(self):
        self.metric = DatasetAndCodeMetric()

    def test_initialization(self):
        self.assertEqual(self.metric.dataset_and_code_score, 0.0)
        self.assertEqual(self.metric.dataset_and_code_score_latency, 0.0)

    def test_get_description(self):
        test_data = {"description": "Test description"}
        result = self.metric.get_description(test_data)
        self.assertEqual(result, "Test description")

        result = self.metric.get_description({})
        self.assertEqual(result, "")

    def test_ml_integration_detection(self):
        test_data = {"tags": ["transformers", "pytorch"]}
        result = self.metric.ml_integration(test_data)
        self.assertTrue(result)

        test_data = {"pipeline_tag": "text-classification"}
        result = self.metric.ml_integration(test_data)
        self.assertTrue(result)

        test_data = {"tags": ["other", "random"]}
        result = self.metric.ml_integration(test_data)
        self.assertFalse(result)

    def test_score_calculation(self):
        test_data = {
            "category": "MODEL",
            "description": "A comprehensive description that is long enough to get good documentation score",
            "example_count": 0,
            "licenses": "apache-2.0",
            "ml_integration": True,
            "engagement": {"downloads": 15000, "likes": 150},
            "has_documentation": True,
            "has_code_examples": True,
            "tags": [],
            "card_data": {},
            "downloads": 15000,
            "likes": 150,
        }

        self.metric.calculate_score(test_data)

        self.assertGreater(self.metric.dataset_and_code_score, 0.5)
        self.assertLessEqual(self.metric.dataset_and_code_score, 1.0)
