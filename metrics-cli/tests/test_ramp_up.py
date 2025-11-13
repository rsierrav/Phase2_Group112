import unittest
from src.metrics.ramp_up_time import RampUpTime


class TestRampUpTime(unittest.TestCase):
    def setUp(self):
        self.metric = RampUpTime()

    def test_get_description_from_metadata_and_card(self):
        parsed = {"metadata": {"description": "Meta desc"}}
        self.assertEqual(self.metric.get_description(parsed), "Meta desc")

        parsed = {"cardData": {"model_description": "Card desc"}}
        self.assertEqual(self.metric.get_description(parsed), "Card desc")

    def test_has_quick_start_guide_from_description(self):
        parsed = {"description": "This is a Quick Start tutorial"}
        self.assertTrue(self.metric.has_quick_start_guide(parsed))

    def test_has_installation_instructions_from_tags_and_siblings(self):
        parsed = {"description": "pip install mypkg"}
        self.assertTrue(self.metric.has_installation_instructions(parsed))

        parsed = {"tags": ["transformers"]}
        self.assertTrue(self.metric.has_installation_instructions(parsed))

        parsed = {"siblings": [{"rfilename": "requirements.txt"}]}
        self.assertTrue(self.metric.has_installation_instructions(parsed))

    def test_has_runnable_examples_from_widget_and_siblings(self):
        parsed = {"widgetData": [{"id": 1}]}
        self.assertTrue(self.metric.has_runnable_examples(parsed))

        parsed = {"transformersInfo": {"auto_model": True}}
        self.assertTrue(self.metric.has_runnable_examples(parsed))

        parsed = {"siblings": [{"rfilename": "example.py"}]}
        self.assertTrue(self.metric.has_runnable_examples(parsed))

    def test_has_minimal_dependencies_from_tags_and_description(self):
        parsed = {"tags": ["pytorch"]}
        self.assertTrue(self.metric.has_minimal_dependencies(parsed))

        parsed = {"description": "This model has no dependencies"}
        self.assertTrue(self.metric.has_minimal_dependencies(parsed))

    def test_model_complexity_from_tags_and_description(self):
        parsed = {"tags": ["bert-large"]}
        self.assertEqual(self.metric.get_model_complexity(parsed), "large")

        parsed = {"tags": ["tiny-model"]}
        self.assertEqual(self.metric.get_model_complexity(parsed), "small")

        parsed = {"description": "This model has 1 billion parameters"}
        self.assertEqual(self.metric.get_model_complexity(parsed), "large")

        parsed = {"description": "A lightweight model"}
        self.assertEqual(self.metric.get_model_complexity(parsed), "small")

        parsed = {}
        self.assertEqual(self.metric.get_model_complexity(parsed), "medium")

    def test_has_clear_documentation_and_siblings(self):
        parsed = {"description": "short"}
        self.assertFalse(self.metric.has_clear_documentation(parsed))

        parsed = {"siblings": [{"rfilename": "README.md"}]}
        self.assertTrue(self.metric.has_clear_documentation(parsed))

    def test_get_data_and_calculate_score(self):
        parsed = {
            "category": "MODEL",
            "description": "This is a Quick Start guide. pip install example.",
            "tags": ["pytorch", "bert-base"],
            "siblings": [{"rfilename": "example.py"}],
        }
        data = self.metric.get_data(parsed)
        self.metric.calculate_score(data)
        self.assertGreater(self.metric.get_score(), 0.0)


if __name__ == "__main__":
    unittest.main()
