import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.metrics.data_quality import DatasetQualityMetric


class TestDatasetQualityMetric(unittest.TestCase):
    def setUp(self):
        self.metric = DatasetQualityMetric()

    def test_initialization(self):
        self.assertEqual(self.metric.dataset_quality, 0.0)
        self.assertEqual(self.metric.dataset_quality_latency, 0.0)

    def test_example_count_extraction(self):
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

    def test_metadata_completeness(self):
        test_data = {
            "cardData": {
                "task_categories": ["text-classification"],
                "language": ["en"],
                "size_categories": ["1K<n<10K"],
                "source_datasets": ["original"],
            }
        }

        result = self.metric.get_metadata_completeness(test_data)
        self.assertAlmostEqual(result, 4 / 6, places=2)

    def test_non_dataset_returns_zero(self):
        test_data = {"category": "MODEL"}
        data = self.metric.get_data(test_data)
        self.assertIsNone(data)
