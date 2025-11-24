import unittest
from src.metrics.dataset_and_code import DatasetAndCodeMetric


class TestDatasetAndCodeMetric(unittest.TestCase):
    def setUp(self):
        self.metric = DatasetAndCodeMetric()

    def test_initialization(self):
        # score attribute isn’t set until calculate_score is called
        # so just check that the object initializes without error
        self.assertIsInstance(self.metric, DatasetAndCodeMetric)

    def test_get_example_count_from_dict(self):
        data = {
            "category": "DATASET",
            "cardData": {"dataset_info": {"splits": [{"num_examples": 42}]}},
        }
        self.assertEqual(self.metric.get_example_count(data), 42)

    def test_get_example_count_from_list(self):
        data = {
            "category": "DATASET",
            "cardData": {"dataset_info": [{"splits": [{"num_examples": 100}]}]},
        }
        self.assertEqual(self.metric.get_example_count(data), 100)

    def test_get_licenses_from_cardData_dict(self):
        data = {"cardData": {"license": "apache-2.0"}}
        # Implementation returns a string, not a list
        self.assertEqual(self.metric.get_licenses(data), "apache-2.0")

    def test_get_licenses_from_list(self):
        data = {"cardData": {"license": ["mit", "apache-2.0"]}}
        result = self.metric.get_licenses(data)
        self.assertIn("mit", result)
        self.assertIn("apache-2.0", result)

    def test_get_licenses_from_tags(self):
        data = {"tags": ["license:mit", "nlp"]}
        result = self.metric.get_licenses(data)
        self.assertIn("mit", result)

    def test_ml_integration_with_pipeline_tag(self):
        data = {"pipeline_tag": "text-classification"}
        self.assertTrue(self.metric.ml_integration(data))

    def test_ml_integration_with_transformersInfo(self):
        data = {"transformersInfo": {"auto_model": True}}
        self.assertTrue(self.metric.ml_integration(data))

    def test_has_documentation_false(self):
        data = {"description": "short"}
        self.assertFalse(self.metric.has_documentation(data))

    def test_has_documentation_with_readme_sibling(self):
        # Need a sufficiently long description to satisfy logic
        data = {
            "description": "This is a dataset with enough documentation to be valid." * 2,
            "siblings": [{"rfilename": "README.md"}],
        }
        self.assertTrue(self.metric.has_documentation(data))

    def test_has_code_examples_with_widgetData(self):
        data = {"widgetData": [{"id": 1}]}
        self.assertTrue(self.metric.has_code_examples(data))

    def test_has_code_examples_with_metadata_widgetData(self):
        data = {"metadata": {"widgetData": [{"id": 2}]}}
        self.assertTrue(self.metric.has_code_examples(data))

    def test_has_code_examples_with_transformersInfo(self):
        data = {"transformersInfo": {"auto_model": True}}
        self.assertTrue(self.metric.has_code_examples(data))

    def test_has_code_examples_with_example_file(self):
        data = {"siblings": [{"rfilename": "example.py"}]}
        self.assertTrue(self.metric.has_code_examples(data))

    def test_score_calculation_sets_score(self):
        # Provide full data dict similar to what get_data would output
        data = {
            "description": "This is a longer description." * 5,
            "has_documentation": True,
            "has_code_examples": False,
            "category": "MODEL",
            "example_count": 0,
            "ml_integration": False,
            "licenses": "apache-2.0",
            "engagement": {"downloads": 0, "likes": 0, "spaces": 0},
        }
        self.metric.calculate_score(data)
        self.assertGreaterEqual(self.metric.get_score(), 0.0)


if __name__ == "__main__":
    unittest.main()
