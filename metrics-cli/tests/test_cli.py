import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
from io import StringIO
from src.cli import validate_github_token, validate_log_file, process_and_score_input_file, run_cli


class TestCLI(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_github_token_missing(self):
        """Test GitHub token validation when token is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_github_token()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("GITHUB_TOKEN not set", mock_stderr.getvalue())

    def test_validate_github_token_empty(self):
        """Test GitHub token validation when token is empty"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "   "}):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_github_token()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("GITHUB_TOKEN not set", mock_stderr.getvalue())

    @patch("requests.get")
    def test_validate_github_token_invalid(self, mock_get):
        """Test GitHub token validation when token is invalid"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"GITHUB_TOKEN": "invalid_token"}):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_github_token()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("Invalid GITHUB_TOKEN", mock_stderr.getvalue())

    @patch("requests.get")
    def test_validate_github_token_network_error(self, mock_get):
        """Test GitHub token validation when network request fails"""
        mock_get.side_effect = Exception("Network error")

        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_github_token()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("GitHub token validation failed", mock_stderr.getvalue())

    @patch("requests.get")
    def test_validate_github_token_valid(self, mock_get):
        """Test GitHub token validation when token is valid"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"GITHUB_TOKEN": "valid_token"}):
            # Should not raise any exception
            validate_github_token()
            mock_get.assert_called_once()

    def test_validate_log_file_missing_env(self):
        """Test log file validation when LOG_FILE env var is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_log_file()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("LOG_FILE not set", mock_stderr.getvalue())

    def test_validate_log_file_parent_not_exist(self):
        """Test log file validation when parent directory doesn't exist"""
        fake_path = "/nonexistent/directory/log.txt"
        with patch.dict(os.environ, {"LOG_FILE": fake_path}):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_log_file()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("parent directory", mock_stderr.getvalue())

    def test_validate_log_file_not_exist(self):
        """Test log file validation when log file doesn't exist"""
        fake_path = os.path.join(self.temp_dir, "nonexistent.log")
        with patch.dict(os.environ, {"LOG_FILE": fake_path}):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    validate_log_file()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("log file", mock_stderr.getvalue())
                self.assertIn("does not exist", mock_stderr.getvalue())

    def test_validate_log_file_not_writable(self):
        """Test log file validation when log file exists but is not writable"""
        log_path = os.path.join(self.temp_dir, "test.log")
        with open(log_path, "w") as f:
            f.write("test")

        with patch.dict(os.environ, {"LOG_FILE": log_path}):
            with patch("os.access", return_value=False):
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    with self.assertRaises(SystemExit) as cm:
                        validate_log_file()
                    self.assertEqual(cm.exception.code, 1)
                    self.assertIn("cannot write to log file", mock_stderr.getvalue())

    @patch("logging.basicConfig")
    def test_validate_log_file_log_level_0(self, mock_basicConfig):
        """Test log file validation with LOG_LEVEL=0 (disabled)"""
        log_path = os.path.join(self.temp_dir, "test.log")
        with open(log_path, "w") as f:
            f.write("test")

        with patch.dict(os.environ, {"LOG_FILE": log_path, "LOG_LEVEL": "0"}):
            with patch("logging.disable") as mock_disable:
                validate_log_file()
                mock_disable.assert_called_once()
                mock_basicConfig.assert_not_called()

    @patch("logging.basicConfig")
    @patch("logging.info")
    def test_validate_log_file_log_level_2(self, mock_info, mock_basicConfig):
        """Test log file validation with LOG_LEVEL=2 (debug)"""
        log_path = os.path.join(self.temp_dir, "test.log")
        with open(log_path, "w") as f:
            f.write("test")

        with patch.dict(os.environ, {"LOG_FILE": log_path, "LOG_LEVEL": "2"}):
            validate_log_file()
            mock_basicConfig.assert_called_once()
            # Check that DEBUG level was used
            args, kwargs = mock_basicConfig.call_args
            self.assertEqual(kwargs["level"], 10)  # logging.DEBUG = 10

    @patch("src.cli.parse_input_file")
    @patch("src.cli.fetch_metadata")
    @patch("src.cli.format_score_row")
    @patch("src.cli.Scorer")
    def test_process_and_score_input_file(
        self, mock_scorer_class, mock_format, mock_fetch, mock_parse
    ):
        """Test the main processing function"""
        # Mock the chain of function calls
        mock_parse.return_value = [
            {"category": "MODEL", "name": "test-model"},
            {"category": "CODE", "name": "test-code"},  # Should be filtered out
        ]

        mock_fetch.return_value = {"name": "test-model", "score": 0.8}
        mock_format.return_value = {"name": "test-model", "net_score": 0.8}
        mock_scorer = MagicMock()
        mock_scorer_class.return_value = mock_scorer

        with patch("builtins.print") as mock_print:
            process_and_score_input_file("test_file.txt")

            # Should only process MODEL entries
            mock_fetch.assert_called_once()
            mock_format.assert_called_once()
            mock_print.assert_called_once()

            # Check that JSON output is compact (no spaces)
            printed_args = mock_print.call_args[0][0]
            self.assertNotIn(" ", printed_args)  # Should be compact JSON

    @patch("src.cli.validate_github_token")
    @patch("src.cli.validate_log_file")
    @patch("src.cli.process_and_score_input_file")
    @patch("os.path.exists")
    def test_run_cli_score_mode(
        self, mock_exists, mock_process, mock_validate_log, mock_validate_token
    ):
        """Test CLI in score mode"""
        mock_exists.return_value = True

        with patch.object(sys, "argv", ["cli.py", "score", "test_file.txt"]):
            run_cli()

            mock_validate_token.assert_called_once()
            mock_validate_log.assert_called_once()
            mock_process.assert_called_once_with("test_file.txt")

    @patch("src.cli.validate_github_token")
    @patch("src.cli.validate_log_file")
    @patch("os.path.exists")
    def test_run_cli_score_mode_file_not_found(
        self, mock_exists, mock_validate_log, mock_validate_token
    ):
        """Test CLI in score mode when file doesn't exist"""
        mock_exists.return_value = False

        with patch.object(sys, "argv", ["cli.py", "score", "nonexistent.txt"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    run_cli()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("file not found", mock_stderr.getvalue())

    @patch("src.cli.validate_github_token")
    @patch("src.cli.validate_log_file")
    @patch("src.cli.process_and_score_input_file")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("os.path.isfile")
    def test_run_cli_dev_mode(
        self,
        mock_isfile,
        mock_listdir,
        mock_isdir,
        mock_process,
        mock_validate_log,
        mock_validate_token,
    ):
        """Test CLI in dev mode (no score argument)"""
        mock_isdir.return_value = True
        mock_listdir.return_value = ["test_input.txt", "other_file.json"]
        mock_isfile.side_effect = lambda path: "test_input.txt" in path

        with patch.object(sys, "argv", ["cli.py"]):
            run_cli()

            mock_validate_token.assert_called_once()
            mock_validate_log.assert_called_once()
            mock_process.assert_called_once()

            # Check the call arguments more flexibly (handle Windows vs Unix paths)
            call_args = mock_process.call_args[0][0]
            self.assertTrue(call_args.endswith("test_input.txt"))
            self.assertIn("input", call_args)

    @patch("src.cli.validate_github_token")
    @patch("src.cli.validate_log_file")
    @patch("os.path.isdir")
    def test_run_cli_input_dir_not_found(self, mock_isdir, mock_validate_log, mock_validate_token):
        """Test CLI when input directory doesn't exist"""
        mock_isdir.return_value = False

        with patch.object(sys, "argv", ["cli.py"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    run_cli()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("input folder", mock_stderr.getvalue())

    @patch("src.cli.validate_github_token")
    @patch("src.cli.validate_log_file")
    @patch("os.path.isdir")
    @patch("os.listdir")
    def test_run_cli_no_input_files(
        self, mock_listdir, mock_isdir, mock_validate_log, mock_validate_token
    ):
        """Test CLI when no input files are found"""
        mock_isdir.return_value = True
        mock_listdir.return_value = []

        with patch.object(sys, "argv", ["cli.py"]):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as cm:
                    run_cli()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn("No files found", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
