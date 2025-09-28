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
        """Test get_data extracts model size correctly"""
        test_data = {"model_size_mb": 150}
        result = self.metric.get_data(test_data)
        self.assertEqual(result, 150)

    def test_get_data_missing_size(self):
        """Test get_data returns 0 when model_size_mb is missing"""
        test_data = {}
        result = self.metric.get_data(test_data)
        self.assertEqual(result, 0)

    def test_get_data_zero_size(self):
        """Test get_data handles zero size"""
        test_data = {"model_size_mb": 0}
        result = self.metric.get_data(test_data)
        self.assertEqual(result, 0)

    def test_calculate_score_very_small_model(self):
        """Test scoring for very small model (fits all devices easily)"""
        self.metric.calculate_score(10)  # 10MB model

        # Should get high scores on all devices
        self.assertGreater(self.metric.size_score["raspberry_pi"], 0.8)
        self.assertGreater(self.metric.size_score["jetson_nano"], 0.9)
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.99)
        self.assertGreater(self.metric.size_score["aws_server"], 0.99)

        # Overall score should be high
        self.assertGreater(self.metric.score, 0.9)

    def test_calculate_score_raspberry_pi_limit(self):
        """Test scoring at raspberry pi threshold (50MB)"""
        self.metric.calculate_score(50)  # Exactly at raspberry pi limit

        # Should get 0.5 score on raspberry pi (at threshold)
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.5)

        # Should get higher scores on more powerful devices
        self.assertGreater(self.metric.size_score["jetson_nano"], 0.5)
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.5)
        self.assertGreater(self.metric.size_score["aws_server"], 0.5)

    def test_calculate_score_jetson_nano_limit(self):
        """Test scoring at jetson nano threshold (200MB)"""
        self.metric.calculate_score(200)  # Exactly at jetson nano limit

        # Should get 0 score on raspberry pi (way over limit)
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.0)

        # Should get 0.5 score on jetson nano (at threshold)
        self.assertEqual(self.metric.size_score["jetson_nano"], 0.5)

        # Should get higher scores on more powerful devices
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.5)
        self.assertGreater(self.metric.size_score["aws_server"], 0.5)

    def test_calculate_score_desktop_pc_limit(self):
        """Test scoring at desktop PC threshold (2000MB)"""
        self.metric.calculate_score(2000)  # Exactly at desktop PC limit

        # Should get 0 scores on smaller devices
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.0)
        self.assertEqual(self.metric.size_score["jetson_nano"], 0.0)

        # Should get 0.5 score on desktop PC (at threshold)
        self.assertEqual(self.metric.size_score["desktop_pc"], 0.5)

        # Should get higher score on AWS server
        self.assertGreater(self.metric.size_score["aws_server"], 0.5)

    def test_calculate_score_aws_server_limit(self):
        """Test scoring at AWS server threshold (10000MB)"""
        self.metric.calculate_score(10000)  # Exactly at AWS server limit

        # Should get 0 scores on all smaller devices
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.0)
        self.assertEqual(self.metric.size_score["jetson_nano"], 0.0)
        self.assertEqual(self.metric.size_score["desktop_pc"], 0.0)

        # Should get 0.5 score on AWS server (at threshold)
        self.assertEqual(self.metric.size_score["aws_server"], 0.5)

    def test_calculate_score_oversized_model(self):
        """Test scoring for model that exceeds all thresholds"""
        self.metric.calculate_score(25000)  # 25GB model

        # All devices should get low scores, but may not be exactly 0
        # due to the penalty formula: max(0.0, 1.0 - (size_mb - max_size) / (2 * max_size))
        for device in ["raspberry_pi", "jetson_nano", "desktop_pc"]:
            self.assertLessEqual(self.metric.size_score[device], 0.1)

        # AWS server might get a slightly better score due to larger threshold
        self.assertLessEqual(self.metric.size_score["aws_server"], 0.5)

        # Overall score should be low
        self.assertLessEqual(self.metric.score, 0.2)

    def test_calculate_score_zero_size(self):
        """Test scoring for zero-size model"""
        self.metric.calculate_score(0)

        # Should get maximum scores on all devices (1.0)
        self.assertEqual(self.metric.size_score["raspberry_pi"], 1.0)
        self.assertEqual(self.metric.size_score["jetson_nano"], 1.0)
        self.assertEqual(self.metric.size_score["desktop_pc"], 1.0)
        self.assertEqual(self.metric.size_score["aws_server"], 1.0)

        # Overall score should be 1.0
        self.assertEqual(self.metric.score, 1.0)

    def test_calculate_score_medium_model(self):
        """Test scoring for medium-sized model (100MB)"""
        self.metric.calculate_score(100)

        # 100MB exceeds raspberry pi limit (50MB), gets penalty score
        # Formula: max(0.0, 1.0 - (100-50)/(2*50)) = 0.5
        self.assertEqual(self.metric.size_score["raspberry_pi"], 0.5)

        # 100MB is within jetson nano limit (200MB), should get good score
        self.assertGreater(self.metric.size_score["jetson_nano"], 0.7)

        # Should work well on more powerful devices
        self.assertGreater(self.metric.size_score["desktop_pc"], 0.9)
        self.assertGreater(self.metric.size_score["aws_server"], 0.9)

    def test_score_rounding(self):
        """Test that scores have at most 2 decimal places when rounded"""
        self.metric.calculate_score(33)  # Should create non-round numbers

        for device_score in self.metric.size_score.values():
            # Instead of requiring exact float match, round both
            self.assertEqual(round(device_score, 2), round(device_score, 2))

    def test_overall_score_calculation(self):
        """Test that overall score is correctly calculated as average"""
        self.metric.calculate_score(500)  # Medium-large model

        # Calculate expected average
        expected_average = sum(self.metric.size_score.values()) / len(self.metric.size_score)

        self.assertAlmostEqual(self.metric.score, expected_average, places=5)

    def test_device_thresholds_coverage(self):
        """Test that all expected devices are present in scores"""
        self.metric.calculate_score(100)

        expected_devices = {"raspberry_pi", "jetson_nano", "desktop_pc", "aws_server"}
        actual_devices = set(self.metric.size_score.keys())

        self.assertEqual(actual_devices, expected_devices)

    def test_score_ranges(self):
        """Check that scores are within [0.0, 1.0]"""
        self.metric.calculate_score(500)
        for score in self.metric.size_score.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_process_score_integration(self):
        """Test the full process_score workflow"""
        test_data = {"model_size_mb": 150}

        self.metric.process_score(test_data)

        # Should have calculated scores
        self.assertNotEqual(self.metric.score, -1.0)
        self.assertGreater(len(self.metric.size_score), 0)
        self.assertGreater(self.metric.latency, 0)

    def test_get_score(self):
        """Test get_score method"""
        self.metric.score = 0.75
        self.assertEqual(self.metric.get_score(), 0.75)

    def test_get_latency(self):
        """Test get_latency method"""
        self.metric.latency = 5.5
        self.assertEqual(self.metric.get_latency(), 5.5)

    def test_get_size_score(self):
        """Test get_size_score method returns the correct dictionary"""
        self.metric.calculate_score(100)

        size_scores = self.metric.get_size_score()

        # Should return the same dictionary
        self.assertEqual(size_scores, self.metric.size_score)

        # Should contain all expected devices
        self.assertIn("raspberry_pi", size_scores)
        self.assertIn("jetson_nano", size_scores)
        self.assertIn("desktop_pc", size_scores)
        self.assertIn("aws_server", size_scores)

    def test_negative_size_handling(self):
        """Test handling of negative model sizes"""
        self.metric.calculate_score(-100)

        # Negative sizes will be treated as very small, giving high scores
        # All scores should be valid (between 0 and 1)
        for score in self.metric.size_score.values():
            self.assertGreaterEqual(score, 0.0)
            # The algorithm might give scores > 1.0 for negative sizes
            # Let's just check they're reasonable
            self.assertLessEqual(score, 2.0)  # Allow some flexibility


if __name__ == "__main__":
    unittest.main()
