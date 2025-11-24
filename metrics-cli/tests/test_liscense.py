import unittest
from src.metrics.license import LicenseMetric


class TestLicenseMetric(unittest.TestCase):

    def setUp(self):
        self.metric = LicenseMetric()

    def test_initialization(self):
        self.assertEqual(self.metric.score, -1.0)
        self.assertEqual(self.metric.latency, -1.0)

    def test_get_data_direct_field(self):
        parsed_data = {"license": "MIT"}
        result = self.metric.get_data(parsed_data)
        self.assertEqual(result, "MIT")

        parsed_data = {"license": "  apache-2.0  "}
        result = self.metric.get_data(parsed_data)
        self.assertEqual(result, "apache-2.0")

        parsed_data = {"license": ""}
        result = self.metric.get_data(parsed_data)
        self.assertIsNone(result)

    def test_calculate_score_high_quality(self):
        self.metric.calculate_score("mit")
        self.assertEqual(self.metric.score, 1.0)

    def test_calculate_score_medium_quality(self):
        self.metric.calculate_score("gpl-3.0")
        self.assertEqual(self.metric.score, 0.7)

    def test_calculate_score_custom(self):
        self.metric.calculate_score("custom-license")
        self.assertEqual(self.metric.score, 0.5)

    def test_calculate_score_unknown(self):
        self.metric.calculate_score("unknown")
        self.assertEqual(self.metric.score, 0.2)

    def test_calculate_score_unrecognized(self):
        self.metric.calculate_score("weird-license")
        self.assertEqual(self.metric.score, 0.2)

    def test_process_score(self):
        parsed_data = {"license": "apache-2.0"}
        self.metric.process_score(parsed_data)

        self.assertEqual(self.metric.get_score(), 1.0)
        self.assertGreaterEqual(self.metric.get_latency(), 0.0)


if __name__ == "__main__":
    unittest.main()
