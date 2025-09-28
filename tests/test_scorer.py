import unittest
from unittest.mock import patch, Mock
from src.scorer import Scorer, run_metric


class TestScorer(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.scorer = Scorer()
        self.sample_metadata = {
            "name": "test-model",
            "category": "MODEL",
            "model_size_mb": 100,
            "license": "MIT",
            "code_url": "https://github.com/owner/repo",
            "dataset_url": "https://huggingface.co/datasets/owner/data",
        }

    def test_initialization(self):
        metric_names = [name for name, _ in self.scorer.metrics]
        expected_metrics = [
            "bus_factor",
            "performance_claims",
            "license",
            "size_score",
            "dataset_and_code_score",
            "dataset_quality",
            "code_quality",
            "ramp_up_time",
        ]
        for expected in expected_metrics:
            self.assertIn(expected, metric_names)

        for metric_name in metric_names:
            self.assertIn(metric_name, self.scorer.weights)

        total_weight = sum(self.scorer.weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)

    def test_score_basic_functionality(self):
        result = self.scorer.score(self.sample_metadata)
        self.assertIn("name", result)
        self.assertIn("category", result)
        self.assertIn("net_score", result)
        self.assertIn("net_score_latency", result)
        for metric_name, _ in self.scorer.metrics:
            self.assertIn(metric_name, result)
            self.assertIn(f"{metric_name}_latency", result)

    def test_score_with_empty_metadata(self):
        empty_metadata = {}
        result = self.scorer.score(empty_metadata)
        self.assertEqual(result["name"], "Unknown")
        self.assertEqual(result["category"], "UNKNOWN")
        self.assertIsInstance(result["net_score"], (int, float))
        self.assertGreater(result["net_score_latency"], 0)

    def test_score_metadata_extraction(self):
        metadata = {"name": "custom-model", "category": "CUSTOM"}
        result = self.scorer.score(metadata)
        self.assertEqual(result["name"], "custom-model")
        self.assertEqual(result["category"], "CUSTOM")

    def test_run_metric_helper_success(self):
        mock_metric = Mock()
        mock_metric.process_score = Mock()
        mock_metric.get_score = Mock(return_value=0.8)
        mock_metric.get_latency = Mock(return_value=15.0)

        metric_info = ("test_metric", mock_metric)
        result = run_metric(metric_info, self.sample_metadata)

        self.assertEqual(result[0], "test_metric")
        self.assertTrue(result[1]["success"])
        self.assertEqual(result[1]["score"], 0.8)
        self.assertEqual(result[1]["latency"], 15.0)

    def test_run_metric_helper_size_score(self):
        mock_metric = Mock()
        mock_metric.process_score = Mock()
        mock_metric.get_size_score = Mock(return_value={"device1": 0.5, "device2": 0.8})
        mock_metric.get_latency = Mock(return_value=20.0)

        metric_info = ("size_score", mock_metric)
        result = run_metric(metric_info, self.sample_metadata)

        self.assertEqual(result[0], "size_score")
        self.assertTrue(result[1]["success"])
        self.assertEqual(result[1]["score"], {"device1": 0.5, "device2": 0.8})

    def test_run_metric_helper_failure(self):
        mock_metric = Mock()
        mock_metric.process_score = Mock(side_effect=Exception("Test error"))

        metric_info = ("test_metric", mock_metric)
        result = run_metric(metric_info, self.sample_metadata)

        self.assertEqual(result[0], "test_metric")
        self.assertFalse(result[1]["success"])
        self.assertEqual(result[1]["score"], -1.0)
        self.assertEqual(result[1]["latency"], -1.0)
        self.assertEqual(result[1]["error"], "Test error")

    def test_run_metric_helper_size_score_failure(self):
        mock_metric = Mock()
        mock_metric.process_score = Mock(side_effect=Exception("Size error"))

        metric_info = ("size_score", mock_metric)
        result = run_metric(metric_info, self.sample_metadata)

        self.assertEqual(result[0], "size_score")
        self.assertFalse(result[1]["success"])
        self.assertEqual(result[1]["score"], {})
        self.assertEqual(result[1]["error"], "Size error")

    def test_score_with_mixed_metric_results(self):
        with patch.object(self.scorer.metrics[0][1], "process_score", side_effect=Exception("Fail")):
            with patch("builtins.print"):
                result = self.scorer.score(self.sample_metadata)
        self.assertIn("net_score", result)
        self.assertIn("net_score_latency", result)
        failed_metric_name = self.scorer.metrics[0][0]
        if failed_metric_name == "size_score":
            self.assertEqual(result[failed_metric_name], {})
        else:
            self.assertEqual(result[failed_metric_name], -1.0)

    def test_net_score_calculation_with_size_dict(self):
        mock_results = {
            "bus_factor": 0.8,
            "performance_claims": 0.7,
            "license": 1.0,
            "size_score": {
                "raspberry_pi": 0.5,
                "jetson_nano": 0.7,
                "desktop_pc": 0.9,
                "aws_server": 1.0,
            },
            "dataset_and_code_score": 0.85,
            "dataset_quality": 0.75,
            "code_quality": 0.9,
            "ramp_up_time": 0.6,
        }

        with patch("src.scorer.run_metric") as mock_run_metric:

            def side_effect(metric_info, metadata):
                name = metric_info[0]
                return name, {"score": mock_results[name], "latency": 10.0, "success": True}

            mock_run_metric.side_effect = side_effect
            result = self.scorer.score(self.sample_metadata)

        self.assertEqual(result["size_score"], mock_results["size_score"])
        self.assertGreater(result["net_score"], 0)
        self.assertLess(result["net_score"], 1.0)

    def test_net_score_all_metrics_failed(self):
        with patch("src.scorer.run_metric") as mock_run_metric:
            mock_run_metric.return_value = (
                "test",
                {"score": -1.0, "latency": -1.0, "success": False},
            )
            result = self.scorer.score(self.sample_metadata)
        self.assertEqual(result["net_score"], -1.0)

    def test_net_score_empty_size_score(self):
        with patch("src.scorer.run_metric") as mock_run_metric:

            def side_effect(metric_info, metadata):
                name = metric_info[0]
                if name == "size_score":
                    return name, {"score": {}, "latency": 10.0, "success": False}
                return name, {"score": 0.5, "latency": 10.0, "success": True}

            mock_run_metric.side_effect = side_effect
            result = self.scorer.score(self.sample_metadata)
        self.assertGreater(result["net_score"], 0)

    def test_metadata_copying(self):
        original_metadata = {"test": "value", "nested": {"key": "value"}}
        mock_metric = Mock()
        mock_metric.process_score = Mock()
        mock_metric.get_score = Mock(return_value=0.5)
        mock_metric.get_latency = Mock(return_value=10.0)
        metric_info = ("test_metric", mock_metric)
        run_metric(metric_info, original_metadata)
        mock_metric.process_score.assert_called_once()
        called_metadata = mock_metric.process_score.call_args[0][0]
        self.assertEqual(called_metadata, original_metadata)
        self.assertIsNot(called_metadata, original_metadata)

    def test_weights_immutability(self):
        original_weights = self.scorer.weights.copy()
        for _ in range(3):
            self.scorer.score(self.sample_metadata)
        self.assertEqual(self.scorer.weights, original_weights)

    def test_concurrent_scoring(self):
        import threading

        results = []

        def score_model():
            result = self.scorer.score(self.sample_metadata)
            results.append(result)

        threads = [threading.Thread(target=score_model) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn("net_score", result)
            self.assertIn("name", result)


if __name__ == "__main__":
    unittest.main()
