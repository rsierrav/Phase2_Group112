import unittest
from src.metrics.protocol import Metric


class TestProtocol(unittest.TestCase):
    def test_process_score_with_dummy_metric(self):
        class DummyMetric:
            def __init__(self):
                self.score = 0.0
                self.latency = 0.0

            def get_data(self, parsed):
                return {"val": 2}

            def calculate_score(self, data):
                self.score = data["val"] * 0.5

            def get_score(self):
                return self.score

            def get_latency(self):
                return self.latency

        dummy = DummyMetric()
        Metric.process_score(dummy, {"val": 2})

        # Score should be set
        self.assertEqual(dummy.get_score(), 1.0)
        # Latency should be recorded
        self.assertGreaterEqual(dummy.get_latency(), 0.0)


if __name__ == "__main__":
    unittest.main()
