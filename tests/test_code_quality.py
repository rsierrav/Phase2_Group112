import unittest
from unittest.mock import patch, MagicMock
from src.metrics.code_quality import code_quality


class TestCodeQualityMetric(unittest.TestCase):
    def setUp(self):
        self.metric = code_quality()

    def test_initialization(self):
        """Metric initializes with sentinel defaults"""
        self.assertEqual(self.metric.score, -1.0)
        self.assertEqual(self.metric.latency, -1.0)

    def test_get_data_non_repo(self):
        """Non-GitHub or missing repo should return default empty evidence"""
        parsed = {"category": "MODEL", "url": "https://huggingface.co/some/model", "code_url": ""}
        result = self.metric.get_data(parsed)
        expected_keys = {
            "has_tests",
            "has_ci",
            "has_lint_config",
            "python_file_count",
            "has_readme",
            "has_packaging",
        }
        self.assertEqual(set(result.keys()), expected_keys)
        self.assertFalse(result["has_tests"])
        self.assertFalse(result["has_ci"])
        self.assertFalse(result["has_lint_config"])
        self.assertEqual(result["python_file_count"], 0)
        self.assertFalse(result["has_readme"])
        self.assertFalse(result["has_packaging"])

    @patch("src.metrics.code_quality.requests.get")
    def test_get_data_fetch_success_and_counts(self, mock_get):
        """Repo tree parsing should detect files and set flags correctly"""
        fake_tree = [
            {"path": "README.md"},
            {"path": "src/model.py"},
            {"path": "notebooks/train.ipynb"},
            {"path": "src/compute.cpp"},
            {"path": "tests/test_model.py"},
            {"path": ".github/workflows/ci.yml"},
            {"path": ".eslintrc"},
            {"path": "package.json"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tree": fake_tree}
        mock_get.return_value = mock_resp

        parsed = {"category": "CODE", "url": "https://github.com/example_owner/example_repo"}
        result = self.metric.get_data(parsed)

        self.assertTrue(result["has_tests"])
        self.assertTrue(result["has_ci"])
        self.assertTrue(result["has_lint_config"])
        self.assertTrue(result["has_readme"])
        self.assertTrue(result["has_packaging"])
        # Only Python files are counted
        self.assertEqual(result["python_file_count"], 1)

    def test_calculate_score_computation(self):
        """Check scoring with representative data"""
        data = {
            "has_tests": True,
            "has_ci": True,
            "has_lint_config": True,
            "python_file_count": 3,
            "has_readme": True,
            "has_packaging": True,
        }

        self.metric.calculate_score(data)
        score = self.metric.get_score()

        # Expected: w_tests*1 + w_ci*1 + w_lint*1 + w_py*(3/20) + w_doc_pack*1
        expected = 0.30 * 1 + 0.25 * 1 + 0.15 * 1 + 0.15 * (3 / 20.0) + 0.15 * 1
        self.assertAlmostEqual(score, expected, places=6)
        self.assertIsInstance(self.metric.get_latency(), float)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)

    def test_calculate_score_no_code_files(self):
        """When no code files and no tests/packaging, score should be 0.0"""
        data = {
            "has_tests": False,
            "has_ci": False,
            "has_lint_config": False,
            "python_file_count": 0,
            "has_readme": False,
            "has_packaging": False,
        }
        self.metric.calculate_score(data)
        self.assertEqual(self.metric.get_score(), 0.0)
        self.assertIsInstance(self.metric.get_latency(), float)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)

    def test_getters(self):
        """Test get_score and get_latency return current values"""
        self.metric.score = 0.42
        self.metric.latency = 321.5
        self.assertEqual(self.metric.get_score(), 0.42)
        self.assertEqual(self.metric.get_latency(), 321.5)


if __name__ == "__main__":
    unittest.main()
