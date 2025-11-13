import unittest
from src.metrics.protocol import Metric


class TestProtocol(unittest.TestCase):
    def test_process_score_with_valid_dummy_metric(self):
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
        self.assertEqual(dummy.get_score(), 1.0)

    def test_process_score_with_get_data_none(self):
        class DummyMetric:
            def __init__(self):
                self.score = 0.0
                self.latency = 0.0

            def get_data(self, parsed):
                return None

            def calculate_score(self, data):
                self.score = 42

            def get_score(self):
                return self.score

            def get_latency(self):
                return self.latency

        dummy = DummyMetric()
        Metric.process_score(dummy, {"val": 2})
        # calculate_score should still run with None data
        self.assertEqual(dummy.get_score(), 42)


if __name__ == "__main__":
    unittest.main()
