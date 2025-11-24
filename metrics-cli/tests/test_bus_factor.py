import unittest
from unittest.mock import patch, MagicMock
from src.metrics.bus_factor import bus_factor


class TestBusFactorMetric(unittest.TestCase):
    def setUp(self):
        self.metric = bus_factor()

    def test_initialization(self):
        """Metric initializes with default sentinel values"""
        self.assertEqual(self.metric.score, -1.0)
        self.assertEqual(self.metric.latency, -1.0)

    def test_get_data_prefetched_commit_authors(self):
        """If parsed_data contains commit_authors, get_data should return them normalized"""
        parsed = {"commit_authors": ["alice", "bob", "alice", "  carol  ", None, ""]}
        result = self.metric.get_data(parsed)
        # Should dedupe and strip whitespace, preserve order of first occurrences
        self.assertEqual(result, ["alice", "bob", "carol"])

    @patch("src.metrics.bus_factor.requests.get")
    def test_get_data_fetch_from_github_success(self, mock_get):
        """get_data should fetch commits from GitHub and return unique authors"""
        # Mock commits response: mix of 'author.login' and fallback commit.author fields
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {
                "author": {"login": "alice"},
                "commit": {"author": {"name": "Alice", "email": "a@example.com"}},
            },
            {"author": None, "commit": {"author": {"name": "bob", "email": "b@example.com"}}},
            {
                "author": {"login": "alice"},
                "commit": {"author": {"name": "Alice", "email": "a@example.com"}},
            },
            {"author": None, "commit": {"author": {"name": None, "email": "c@example.com"}}},
        ]
        mock_get.return_value = mock_resp

        parsed = {"code_url": "https://github.com/example_owner/example_repo"}
        result = self.metric.get_data(parsed)

        # Expect deduped login names and fallbacks, preserving first seen order:
        # first 'alice' (from author.login), then 'bob' (commit.author.name), then 'c@example.com'
        self.assertEqual(result, ["alice", "bob", "c@example.com"])

    @patch("src.metrics.bus_factor.requests.get")
    def test_get_data_fetch_non_200(self, mock_get):
        """Non-200 from GitHub should lead to empty authors list"""
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.json.return_value = {"message": "forbidden"}
        mock_get.return_value = mock_resp

        parsed = {"code_url": "https://github.com/example_owner/example_repo"}
        result = self.metric.get_data(parsed)
        self.assertEqual(result, [])

    def test_get_data_invalid_url(self):
        """Non-GitHub or invalid code_url returns empty list"""
        parsed = {"code_url": "https://notgithub.com/user/repo"}
        result = self.metric.get_data(parsed)
        self.assertEqual(result, [])

        parsed2 = {"code_url": ""}
        result2 = self.metric.get_data(parsed2)
        self.assertEqual(result2, [])

    def test_calculate_score_scaling(self):
        """calculate_score should scale with unique authors according to /50 rule"""
        # 0 authors -> score 0.0
        self.metric.calculate_score([])
        self.assertEqual(self.metric.get_score(), 0.0)

        # 1 unique author -> 1/50
        self.metric.calculate_score(["alice"])
        self.assertAlmostEqual(self.metric.get_score(), 1 / 50.0, places=8)

        # 2 unique authors -> 2/50
        self.metric.calculate_score(["alice", "bob"])
        self.assertAlmostEqual(self.metric.get_score(), 2 / 50.0, places=8)

        # 50 unique authors -> 1.0
        many = [f"user{i}" for i in range(50)]
        self.metric.calculate_score(many)
        self.assertEqual(self.metric.get_score(), 1.0)

        # >50 authors still 1.0
        many_plus = [f"user{i}" for i in range(60)]
        self.metric.calculate_score(many_plus)
        self.assertEqual(self.metric.get_score(), 1.0)

    def test_process_score_sets_latency_and_score(self):
        """process_score should populate score and latency (latency >= 0)"""
        # Use pre-fetched commit_authors to avoid network calls
        parsed = {"commit_authors": ["alice", "bob", "carol"]}
        self.metric.process_score(parsed)
        # Score should be 3/50
        self.assertAlmostEqual(self.metric.get_score(), 3 / 50.0, places=8)
        # Latency should be measured and non-negative (float milliseconds)
        self.assertIsInstance(self.metric.get_latency(), float)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)

    def test_getters(self):
        """Test get_score and get_latency return current values"""
        self.metric.score = 0.77
        self.metric.latency = 123.45
        self.assertEqual(self.metric.get_score(), 0.77)
        self.assertEqual(self.metric.get_latency(), 123.45)


if __name__ == "__main__":
    unittest.main()
