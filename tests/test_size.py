import unittest
from src.metrics.size import SizeMetric


class TestSizeMetric(unittest.TestCase):
    def setUp(self):
        self.metric = SizeMetric()

    def test_initialization(self):
        """Test that metric initializes with correct default values"""
        self.assertEqual(self.metric.score, -1.0)
        self.assertEqual(self.metric.latency, -1.0)
        self.assertEqual(self.metric.size_score, {})

    def test_get_data_with_model_size(self):
        test_data = {"model_size_mb": 150}
        result = self.metric.get_data(test_data)
        self.assertEqual(result, 150)

    def test_get_data_missing_size(self):
        test_data = {}
        result = self.metric.get_data(test_data)
        self.assertEqual(result, 0)

    def test_get_data_zero_size(self):
        test_data = {"model_size_mb": 0}
        result = self.metric.get_data(test_data)
        self.assertEqual(result, 0)

    def test_calculate_score_very_small_model(self):
        self.metric.calculate_score(10)
        # All devices should have high scores but < 1.0
        self.assertGreater(self.metric.size_score["raspberry_pi"], 0.8)
        self.assertGreater(self.metric.size_score["jetson_nano"], 0.9)
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.99)
        self.assertGreater(self.metric.size_score["aws_server"], 0.99)
        self.assertGreater(self.metric.score, 0.9)

    def test_calculate_score_raspberry_pi_limit(self):
        self.metric.calculate_score(50)
        # At threshold = 0.5
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.5)
        self.assertGreater(self.metric.size_score["jetson_nano"], 0.5)

    def test_calculate_score_jetson_nano_limit(self):
        self.metric.calculate_score(200)
        # Raspberry Pi should have small but nonzero score now
        self.assertGreaterEqual(self.metric.size_score["raspberry_pi"], 0.0)
        self.assertEqual(self.metric.size_score["jetson_nano"], 0.5)
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.5)

    def test_calculate_score_desktop_pc_limit(self):
        self.metric.calculate_score(2000)
        self.assertGreaterEqual(self.metric.size_score["raspberry_pi"], 0.0)
        self.assertGreaterEqual(self.metric.size_score["jetson_nano"], 0.0)
        self.assertEqual(self.metric.size_score["desktop_pc"], 0.5)

    def test_calculate_score_aws_server_limit(self):
        self.metric.calculate_score(10000)
        self.assertGreaterEqual(self.metric.size_score["raspberry_pi"], 0.0)
        self.assertGreaterEqual(self.metric.size_score["jetson_nano"], 0.0)
        self.assertGreaterEqual(self.metric.size_score["desktop_pc"], 0.0)
        self.assertEqual(self.metric.size_score["aws_server"], 0.5)

    def test_calculate_score_oversized_model(self):
        self.metric.calculate_score(25000)
        for device in ["raspberry_pi", "jetson_nano", "desktop_pc"]:
            self.assertLessEqual(self.metric.size_score[device], 0.5)
        self.assertLessEqual(self.metric.size_score["aws_server"], 0.5)
        self.assertLessEqual(self.metric.score, 0.5)

    def test_calculate_score_zero_size(self):
        self.metric.calculate_score(0)
        # Now expected = 0.0 (new implementation)
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.0)
        self.assertEqual(self.metric.size_score["jetson_nano"], 0.0)
        self.assertEqual(self.metric.size_score["desktop_pc"], 0.0)
        self.assertEqual(self.metric.size_score["aws_server"], 0.0)
        self.assertEqual(self.metric.score, 0.0)

    def test_calculate_score_medium_model(self):
        self.metric.calculate_score(100)
        # According to new formula: Raspberry Pi = 0.25
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.25)
        self.assertGreater(self.metric.size_score["jetson_nano"], 0.7)
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.9)

    def test_score_rounding(self):
        self.metric.calculate_score(33)
        for device_score in self.metric.size_score.values():
            self.assertEqual(device_score, round(device_score, 2))

    def test_overall_score_calculation(self):
        self.metric.calculate_score(500)
        expected_average = round(sum(self.metric.size_score.values()) / len(self.metric.size_score), 2)
        self.assertEqual(self.metric.score, expected_average)

    def test_device_thresholds_coverage(self):
        self.metric.calculate_score(100)
        expected_devices = {"raspberry_pi", "jetson_nano", "desktop_pc", "aws_server"}
        self.assertEqual(set(self.metric.size_score.keys()), expected_devices)

    def test_score_ranges(self):
        self.metric.calculate_score(500)
        for score in self.metric.size_score.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_process_score_integration(self):
        test_data = {"model_size_mb": 150}
        self.metric.process_score(test_data)
        self.assertNotEqual(self.metric.score, -1.0)
        self.assertGreater(len(self.metric.size_score), 0)
        self.assertGreater(self.metric.latency, 0)

    def test_get_score(self):
        self.metric.score = 0.75
        self.assertEqual(self.metric.get_score(), 0.75)

    def test_get_latency(self):
        self.metric.latency = 5.5
        self.assertEqual(self.metric.get_latency(), 5.5)

    def test_get_size_score(self):
        self.metric.calculate_score(100)
        size_scores = self.metric.get_size_score()
        self.assertEqual(size_scores, self.metric.size_score)
        self.assertIn("raspberry_pi", size_scores)
        self.assertIn("jetson_nano", size_scores)
        self.assertIn("desktop_pc", size_scores)
        self.assertIn("aws_server", size_scores)

    def test_negative_size_handling(self):
        self.metric.calculate_score(-100)
        for score in self.metric.size_score.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
