import unittest
import json
from unittest.mock import MagicMock, patch
from src.utils.output_format import (
    print_score_table,
    format_score_row,
    print_score_table_as_json,
    TABLE_COLUMNS,
)


class TestOutputFormat(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.sample_metadata = {"name": "test-model", "category": "MODEL", "model_size_mb": 100.5}

        self.sample_scorer_result = {
            "name": "test-model",
            "category": "MODEL",
            "net_score": 0.85,
            "net_score_latency": 150.75,
            "ramp_up_time": 0.7,
            "ramp_up_time_latency": 45.3,
            "bus_factor": 0.8,
            "bus_factor_latency": 30.9,
            "performance_claims": 0.9,
            "performance_claims_latency": 25.1,
            "license": 1.0,
            "license_latency": 5.8,
            "size_score": {
                "raspberry_pi": 0.2,
                "jetson_nano": 0.5,
                "desktop_pc": 0.9,
                "aws_server": 1.0,
            },
            "size_score_latency": 12.4,
            "dataset_and_code_score": 0.75,
            "dataset_and_code_score_latency": 88.2,
            "dataset_quality": 0.65,
            "dataset_quality_latency": 200.9,
            "code_quality": 0.95,
            "code_quality_latency": 33.7,
        }

    def test_print_score_table(self):
        """Test print_score_table function"""
        test_rows = [{"name": "model1", "score": 0.8}, {"name": "model2", "score": 0.6}]

        with patch("builtins.print") as mock_print:
            print_score_table(test_rows)

            # Should print JSON with indentation
            mock_print.assert_called_once()
            printed_content = mock_print.call_args[0][0]

            # Should be valid JSON
            parsed = json.loads(printed_content)
            self.assertEqual(parsed, test_rows)

            # Should have indentation (pretty printed)
            self.assertIn("\n", printed_content)
            self.assertIn("    ", printed_content)  # Should have 4-space indentation

    def test_print_score_table_as_json(self):
        """Test print_score_table_as_json function (should be same as print_score_table)"""
        test_rows = [{"name": "model1", "score": 0.8}]

        with patch("builtins.print") as mock_print:
            print_score_table_as_json(test_rows)

            mock_print.assert_called_once()
            printed_content = mock_print.call_args[0][0]
            parsed = json.loads(printed_content)
            self.assertEqual(parsed, test_rows)

    def test_format_score_row_complete_data(self):
        """Test format_score_row with complete scorer results"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = self.sample_scorer_result

        result = format_score_row(self.sample_metadata, mock_scorer)

        # Check that scorer was called with metadata
        mock_scorer.score.assert_called_once_with(self.sample_metadata)

        # Check basic fields
        self.assertEqual(result["name"], "test-model")
        self.assertEqual(result["category"], "MODEL")

        # Check score rounding (should be 2 decimal places)
        self.assertEqual(result["net_score"], 0.85)
        self.assertEqual(result["ramp_up_time"], 0.7)

        # Check latency rounding (should be whole numbers)
        self.assertEqual(result["net_score_latency"], 151)  # 150.75 -> 151
        self.assertEqual(result["ramp_up_time_latency"], 45)  # 45.3 -> 45
        self.assertEqual(result["dataset_quality_latency"], 201)  # 200.9 -> 201

        # Check size_score structure
        self.assertIsInstance(result["size_score"], dict)
        self.assertEqual(result["size_score"]["raspberry_pi"], 0.2)
        self.assertEqual(result["size_score"]["jetson_nano"], 0.5)
        self.assertEqual(result["size_score"]["desktop_pc"], 0.9)
        self.assertEqual(result["size_score"]["aws_server"], 1.0)

    def test_format_score_row_missing_data(self):
        """Test format_score_row with missing scorer data"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {
            "name": "incomplete-model",
            "category": "MODEL",
            # Missing most fields
        }

        result = format_score_row(self.sample_metadata, mock_scorer)

        # Should have default values
        self.assertEqual(result["name"], "incomplete-model")
        self.assertEqual(result["category"], "MODEL")
        self.assertEqual(result["net_score"], -1)
        self.assertEqual(result["ramp_up_time"], -1)
        self.assertEqual(result["license"], -1)

        # Size score should have all devices with default values
        self.assertEqual(result["size_score"]["raspberry_pi"], -1)
        self.assertEqual(result["size_score"]["jetson_nano"], -1)
        self.assertEqual(result["size_score"]["desktop_pc"], -1)
        self.assertEqual(result["size_score"]["aws_server"], -1)

    def test_format_score_row_invalid_data_types(self):
        """Test format_score_row with invalid data types"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {
            "name": "test-model",
            "category": "MODEL",
            "net_score": "invalid_string",  # Invalid type
            "net_score_latency": None,  # Invalid type
            "license": [1, 2, 3],  # Invalid type
            "size_score": {},  # Empty dict
        }

        result = format_score_row(self.sample_metadata, mock_scorer)

        # as_float() returns -1 for invalid types when default is -1
        self.assertEqual(result["net_score"], -1)  # Changed from 0.0 to -1
        self.assertEqual(result["net_score_latency"], -1)  # Changed from 0.0 to -1
        self.assertEqual(result["license"], -1)  # Changed from 0.0 to -1

        # Size score should still be a dict with defaults
        self.assertIsInstance(result["size_score"], dict)
        self.assertEqual(result["size_score"]["raspberry_pi"], -1)

    def test_format_score_row_edge_case_values(self):
        """Test format_score_row with edge case numeric values"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {
            "name": "edge-case-model",
            "category": "MODEL",
            "net_score": 0.999999,  # Should round to 1.00
            "net_score_latency": 45.6,  # Should round to 46
            "license": 0.001,  # Should round to 0.00
            "license_latency": 0.4,  # Should round to 0
            "size_score": {
                "raspberry_pi": 0.12345,  # Should round to 0.12
                "jetson_nano": 0.999,  # Should round to 1.00
                "desktop_pc": 1.000001,  # Should round to 1.00
                "aws_server": 0,
            },
        }

        result = format_score_row(self.sample_metadata, mock_scorer)

        # Check rounding behavior
        self.assertEqual(result["net_score"], 1.0)  # 0.999999 -> 1.00
        self.assertEqual(result["net_score_latency"], 46)  # 45.6 -> 46
        self.assertEqual(result["license"], 0.0)  # 0.001 -> 0.00
        self.assertEqual(result["license_latency"], 0)  # 0.4 -> 0

        # Check size score rounding
        self.assertEqual(result["size_score"]["raspberry_pi"], 0.12)
        self.assertEqual(result["size_score"]["jetson_nano"], 1.0)
        self.assertEqual(result["size_score"]["desktop_pc"], 1.0)
        self.assertEqual(result["size_score"]["aws_server"], 0.0)

    def test_format_score_row_all_table_columns_present(self):
        """Test that format_score_row includes all TABLE_COLUMNS"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {"name": "test", "category": "MODEL"}

        result = format_score_row(self.sample_metadata, mock_scorer)

        # Check that all expected columns are present
        for column in TABLE_COLUMNS:
            self.assertIn(column, result, f"Column {column} missing from result")

    def test_format_score_row_unknown_metadata(self):
        """Test format_score_row with unknown/missing metadata"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {}  # Empty result

        result = format_score_row({}, mock_scorer)  # Empty metadata

        # Should have defaults
        self.assertEqual(result["name"], "unknown")
        self.assertEqual(result["category"], "unknown")
        self.assertEqual(result["net_score"], -1)

    def test_format_score_row_partial_size_score(self):
        """Test format_score_row with partial size_score data"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {
            "name": "partial-model",
            "category": "MODEL",
            "size_score": {
                "raspberry_pi": 0.5,
                "desktop_pc": 0.8,
                # Missing jetson_nano and aws_server
            },
        }

        result = format_score_row(self.sample_metadata, mock_scorer)

        # Should fill in missing size score entries
        self.assertEqual(result["size_score"]["raspberry_pi"], 0.5)
        self.assertEqual(result["size_score"]["desktop_pc"], 0.8)
        self.assertEqual(result["size_score"]["jetson_nano"], -1)  # Default
        self.assertEqual(result["size_score"]["aws_server"], -1)  # Default

    def test_format_score_row_latency_rounding_boundaries(self):
        """Test latency rounding at boundary values"""
        mock_scorer = MagicMock()
        mock_scorer.score.return_value = {
            "name": "boundary-model",
            "category": "MODEL",
            "net_score_latency": 10.5,  # Python rounds 10.5 to 10 (round half to even)
            "license_latency": 20.4,  # Should round to 20
            "bus_factor_latency": 30.6,  # Should round to 31
            "size_score_latency": 40.0,  # Should stay 40
        }

        result = format_score_row(self.sample_metadata, mock_scorer)

        # Check rounding behavior for latencies
        self.assertEqual(result["net_score_latency"], 10)  # 10.5 -> 10 (not 11!)
        self.assertEqual(result["license_latency"], 20)  # 20.4 -> 20
        self.assertEqual(result["bus_factor_latency"], 31)  # 30.6 -> 31
        self.assertEqual(result["size_score_latency"], 40)  # 40.0 -> 40

    def test_table_columns_constant(self):
        """Test that TABLE_COLUMNS contains expected columns"""
        expected_columns = {
            "name",
            "category",
            "net_score",
            "net_score_latency",
            "ramp_up_time",
            "ramp_up_time_latency",
            "bus_factor",
            "bus_factor_latency",
            "performance_claims",
            "performance_claims_latency",
            "license",
            "license_latency",
            "size_score",
            "size_score_latency",
            "dataset_and_code_score",
            "dataset_and_code_score_latency",
            "dataset_quality",
            "dataset_quality_latency",
            "code_quality",
            "code_quality_latency",
        }

        self.assertEqual(set(TABLE_COLUMNS), expected_columns)
        self.assertEqual(len(TABLE_COLUMNS), len(expected_columns))


if __name__ == "__main__":
    unittest.main()
