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
            "language_counts",
            "total_code_files",
            "has_readme",
            "has_packaging",
        }
        self.assertEqual(set(result.keys()), expected_keys)
        self.assertFalse(result["has_tests"])
        self.assertFalse(result["has_ci"])
        self.assertFalse(result["has_lint_config"])
        self.assertEqual(result["language_counts"], {})
        self.assertEqual(result["total_code_files"], 0)
        self.assertFalse(result["has_readme"])
        self.assertFalse(result["has_packaging"])

    @patch("src.metrics.code_quality.requests.get")
    def test_get_data_fetch_success_and_language_counts(self, mock_get):
        """Repo tree parsing should detect languages, tests, CI, lint, packaging, and README"""
        # Build a fake git tree with representative paths
        fake_tree = [
            {"path": "README.md"},
            {"path": "src/model.py"},
            {"path": "notebooks/train.ipynb"},
            {"path": "src/compute.cpp"},
            {"path": "tests/test_model.py"},
            {"path": ".github/workflows/ci.yml"},
            {"path": ".eslintrc"},
            {"path": "package.json"},  # packaging (node)
            {"path": "Dockerfile"},
            {"path": "examples/example.ipynb"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"tree": fake_tree}
        mock_get.return_value = mock_resp

        parsed = {"category": "CODE", "url": "https://github.com/example_owner/example_repo"}
        result = self.metric.get_data(parsed)

        # Language counts: Python (.py) => 1, Notebook (.ipynb) => 2, C++ (.cpp) => 1
        # Note: examples/example.ipynb and notebooks/train.ipynb -> 2 notebooks
        self.assertIn("Python", result["language_counts"])
        self.assertIn("Notebook", result["language_counts"])
        self.assertIn("C++", result["language_counts"])
        self.assertEqual(result["language_counts"]["Python"], 1)
        self.assertEqual(result["language_counts"]["Notebook"], 2)
        self.assertEqual(result["language_counts"]["C++"], 1)

        # Derived flags
        self.assertTrue(result["has_tests"])
        self.assertTrue(result["has_ci"])
        self.assertTrue(result["has_lint_config"])
        self.assertTrue(result["has_readme"])
        self.assertTrue(result["has_packaging"])

        # total_code_files should be sum of language_counts = 4
        self.assertEqual(result["total_code_files"], 4)

    def test_calculate_score_computation_with_diversity_bonus(self):
        """
        Given synthetic data with:
          - has_tests=True
          - has_ci=True
          - has_lint_config=True
          - language_counts: 3 languages, total_files=3
          - has_readme=True
          - has_packaging=True
        Expect:
          s_tests=1, s_ci=1, s_lint=1
          s_code = total_files/50 = 3/50 = 0.06
          diversity_bonus = (3/5)*0.2 = 0.12 -> s_code = 0.18
          s_doc_pack = 1.0
          score = 0.3*1 + 0.25*1 + 0.15*1 + 0.15*0.18 + 0.15*1 = ~0.877
        """
        data = {
            "has_tests": True,
            "has_ci": True,
            "has_lint_config": True,
            "language_counts": {"Python": 1, "Notebook": 1, "C++": 1},
            "total_code_files": 3,
            "has_readme": True,
            "has_packaging": True,
        }

        self.metric.calculate_score(data)
        score = self.metric.get_score()

        # Compute expected score numerically
        s_tests = 1.0
        s_ci = 1.0
        s_lint = 1.0
        s_code = min(1.0, 3 / 50.0)
        diversity_bonus = min(0.2, (3 / 5.0) * 0.2)
        s_code = min(1.0, s_code + diversity_bonus)
        s_doc_pack = 1.0

        expected = (
            (0.30 * s_tests)
            + (0.25 * s_ci)
            + (0.15 * s_lint)
            + (0.15 * s_code)
            + (0.15 * s_doc_pack)
        )

        # Allow small floating rounding tolerance
        self.assertAlmostEqual(score, expected, places=6)
        # Latency should be set and non-negative
        self.assertIsInstance(self.metric.get_latency(), float)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)

    def test_calculate_score_no_code_files(self):
        """When there are no code files and no tests/packaging, score should be low (0.0)"""
        data = {
            "has_tests": False,
            "has_ci": False,
            "has_lint_config": False,
            "language_counts": {},
            "total_code_files": 0,
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
