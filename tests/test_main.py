import unittest
import sys
from unittest.mock import patch
import src.main as main


class TestMainCLI(unittest.TestCase):
    def setUp(self):
        self.orig_argv = sys.argv.copy()

    def tearDown(self):
        sys.argv = self.orig_argv

    @patch("src.main.os.path.isfile", return_value=True)
    @patch("src.main.parse_input_file", return_value=[{"category": "MODEL"}])
    @patch("src.main.fetch_metadata", return_value={"category": "MODEL"})
    @patch("src.main.format_score_row", return_value={"name": "dummy"})
    def test_score_command(self, mock_format, mock_fetch, mock_parse, mock_isfile):
        sys.argv = ["main.py", "score", "input.txt"]
        with patch("builtins.print") as mock_print:
            main.main()
            mock_print.assert_called()

    def test_usage_no_args(self):
        sys.argv = ["main.py"]
        with self.assertRaises(SystemExit):
            main.main()

    @patch("src.main.parse_input_file", return_value=[{"category": "MODEL"}])
    @patch("src.main.fetch_metadata", return_value={"category": "MODEL"})
    @patch("src.main.format_score_row", return_value={"name": "dummy"})
    def test_http_input(self, mock_format, mock_fetch, mock_parse):
        sys.argv = ["main.py", "https://huggingface.co/foo/bar"]
        with patch("builtins.print") as mock_print:
            main.main()
            mock_print.assert_called()

    @patch("src.main.os.path.isfile", return_value=True)
    @patch("src.main.parse_input_file", return_value=[{"category": "MODEL"}])
    @patch("src.main.fetch_metadata", return_value={"category": "MODEL"})
    @patch("src.main.format_score_row", return_value={"name": "dummy"})
    def test_file_input(self, mock_format, mock_fetch, mock_parse, mock_isfile):
        sys.argv = ["main.py", "input.txt"]
        with patch("builtins.print") as mock_print:
            main.main()
            mock_print.assert_called()


if __name__ == "__main__":
    unittest.main()
