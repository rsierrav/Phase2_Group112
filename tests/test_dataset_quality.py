import unittest
import os
from unittest.mock import patch, MagicMock
from src.metrics.dataset_quality import DatasetQualityMetric


class TestDatasetQualityMetric(unittest.TestCase):
    def setUp(self):
        self.metric = DatasetQualityMetric()

    def test_initialization(self):
        """Test that metric initializes with correct default values"""
        self.assertEqual(self.metric.score, -1.0)
        self.assertEqual(self.metric.latency, -1.0)

    def test_get_data_with_urls(self):
        """Test get_data extracts URLs correctly"""
        test_data = {
            "dataset_url": "https://huggingface.co/datasets/test",
            "code_url": "https://github.com/test/repo",
        }

        result = self.metric.get_data(test_data)
        expected = {
            "dataset_url": "https://huggingface.co/datasets/test",
            "code_url": "https://github.com/test/repo",
        }
        self.assertEqual(result, expected)

    def test_get_data_empty(self):
        """Test get_data with empty/missing data"""
        test_data = {}
        result = self.metric.get_data(test_data)
        expected = {"dataset_url": "", "code_url": ""}
        self.assertEqual(result, expected)

    def test_get_description(self):
        """Test description extraction"""
        test_data = {"description": "Test dataset description"}
        result = self.metric.get_description(test_data)
        self.assertEqual(result, "Test dataset description")

        # Test empty description
        result = self.metric.get_description({})
        self.assertEqual(result, "")

    def test_example_count_extraction_basic(self):
        """Test basic example count extraction from dataset splits"""
        test_data = {
            "category": "DATASET",
            "cardData": {
                "dataset_info": {
                    "splits": [
                        {"name": "train", "num_examples": 1000},
                        {"name": "test", "num_examples": 200},
                    ]
                }
            },
        }

        result = self.metric.get_example_count(test_data)
        self.assertEqual(result, 1200)

    def test_example_count_extraction_list_format(self):
        """Test example count extraction when dataset_info is a list"""
        test_data = {
            "category": "DATASET",
            "cardData": {
                "dataset_info": [
                    {
                        "splits": [
                            {"name": "train", "num_examples": 500},
                            {"name": "validation", "num_examples": 100},
                        ]
                    },
                    {
                        "splits": [
                            {"name": "test", "num_examples": 200},
                        ]
                    },
                ]
            },
        }

        result = self.metric.get_example_count(test_data)
        self.assertEqual(result, 800)

    def test_example_count_non_dataset(self):
        """Test example count returns 0 for non-dataset categories"""
        test_data = {"category": "MODEL"}
        result = self.metric.get_example_count(test_data)
        self.assertEqual(result, 0)

    def test_example_count_malformed_data(self):
        """Test example count handles malformed data gracefully"""
        test_data = {
            "category": "DATASET",
            "cardData": {
                "dataset_info": {
                    "splits": [
                        {"name": "train"},  # Missing num_examples
                        {"name": "test", "num_examples": None},  # None value
                    ]
                }
            },
        }

        result = self.metric.get_example_count(test_data)
        self.assertEqual(result, 0)

    def test_metadata_completeness_full(self):
        """Test metadata completeness with all fields present"""
        test_data = {
            "cardData": {
                "task_categories": ["text-classification"],
                "language": ["en"],
                "size_categories": ["1K<n<10K"],
                "source_datasets": ["original"],
                "annotations_creators": ["expert-generated"],
                "language_creators": ["crowdsourced"],
            }
        }

        result = self.metric.get_metadata_completeness(test_data)
        self.assertEqual(result, 1.0)  # All 6 fields present

    def test_metadata_completeness_partial(self):
        """Test metadata completeness with some fields present"""
        test_data = {
            "cardData": {
                "task_categories": ["text-classification"],
                "language": ["en"],
                "size_categories": ["1K<n<10K"],
                "source_datasets": ["original"],
                # Missing 2 fields
            }
        }

        result = self.metric.get_metadata_completeness(test_data)
        self.assertAlmostEqual(result, 4 / 6, places=2)

    def test_metadata_completeness_empty_lists(self):
        """Test metadata completeness ignores empty lists"""
        test_data = {
            "cardData": {
                "task_categories": [],  # Empty list shouldn't count
                "language": ["en"],
                "size_categories": "",  # Empty string shouldn't count
                "source_datasets": ["original"],
            }
        }

        result = self.metric.get_metadata_completeness(test_data)
        self.assertAlmostEqual(result, 2 / 6, places=2)

    def test_calculate_score_no_api_key(self):
        """Test calculate_score when no API key is available"""
        with patch.dict(os.environ, {}, clear=True):  # Clear environment
            data = {"dataset_url": "test", "code_url": "test"}

            self.metric.calculate_score(data)

            self.assertEqual(self.metric.score, 0.33)
            self.assertGreaterEqual(self.metric.latency, 0)

    @patch("requests.post")
    def test_calculate_score_api_success(self, mock_post):
        """Test calculate_score with successful API call"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "0.85"}}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEN_AI_STUDIO_API_KEY": "test_key"}):
            data = {"dataset_url": "test", "code_url": "test"}

            self.metric.calculate_score(data)

            self.assertEqual(self.metric.score, 0.85)
            self.assertGreaterEqual(self.metric.latency, 0)

    @patch("requests.post")
    def test_calculate_score_api_failure(self, mock_post):
        """Test calculate_score when API call fails"""
        # Mock failed API response
        mock_post.side_effect = Exception("API Error")

        with patch.dict(os.environ, {"GEN_AI_STUDIO_API_KEY": "test_key"}):
            data = {"dataset_url": "test", "code_url": "test"}

            self.metric.calculate_score(data)

            self.assertEqual(self.metric.score, 0.11)  # Fallback score
            self.assertGreaterEqual(self.metric.latency, 0)

    @patch("requests.post")
    def test_calculate_score_invalid_response(self, mock_post):
        """Test calculate_score with invalid API response"""
        # Mock API response with invalid score
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "invalid_number"}}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEN_AI_STUDIO_API_KEY": "test_key"}):
            data = {"dataset_url": "test", "code_url": "test"}

            self.metric.calculate_score(data)

            self.assertEqual(self.metric.score, 0.11)  # Fallback score

    @patch("requests.post")
    def test_calculate_score_bounds_checking(self, mock_post):
        """Test that calculate_score properly bounds the score between 0 and 1"""
        # Test score above 1.0
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "1.5"}}]}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEN_AI_STUDIO_API_KEY": "test_key"}):
            data = {"dataset_url": "test", "code_url": "test"}

            self.metric.calculate_score(data)

            self.assertEqual(self.metric.score, 1.0)  # Should be clamped to 1.0

    def test_process_score_integration(self):
        """Test the full process_score workflow"""
        test_data = {
            "dataset_url": "https://huggingface.co/datasets/test",
            "code_url": "https://github.com/test/repo",
        }

        with patch.dict(os.environ, {}, clear=True):  # No API key
            self.metric.process_score(test_data)

            self.assertEqual(self.metric.score, 0.33)
            self.assertGreater(self.metric.latency, 0)

    def test_get_score_and_latency(self):
        """Test getter methods"""
        self.metric.score = 0.75
        self.metric.latency = 150.0

        self.assertEqual(self.metric.get_score(), 0.75)
        self.assertEqual(self.metric.get_latency(), 150.0)


if __name__ == "__main__":
    unittest.main()
