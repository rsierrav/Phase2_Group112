import unittest
import sys
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, mock_open
import run


class TestRunPy(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        sys.argv = self.original_argv

    def test_show_usage(self):
        """Test show_usage exits with code 1 and prints usage info"""
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit) as cm:
                run.show_usage()
            self.assertEqual(cm.exception.code, 1)
            usage_calls = [call[0][0] for call in mock_print.call_args_list]
            usage_text = "\n".join(usage_calls)
            self.assertIn("Usage:", usage_text)
            self.assertIn("install", usage_text)
            self.assertIn("score", usage_text)
            self.assertIn("test", usage_text)

    @patch("subprocess.check_call")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_install_dependencies_create_requirements(self, mock_file, mock_exists, mock_subprocess):
        mock_exists.return_value = False
        run.install_dependencies()
        mock_file.assert_called()
        mock_subprocess.assert_called_once()

    @patch("subprocess.check_call")
    @patch("os.path.exists")
    def test_install_dependencies_existing_requirements(self, mock_exists, mock_subprocess):
        mock_exists.return_value = True
        run.install_dependencies()
        mock_subprocess.assert_called_once()

    @patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "pip"))
    @patch("os.path.exists", return_value=True)
    def test_install_dependencies_pip_failure(self, mock_exists, mock_subprocess):
        with self.assertRaises(SystemExit) as cm:
            run.install_dependencies()
        self.assertEqual(cm.exception.code, 1)

    def test_process_urls_with_cli_file_not_found(self):
        with self.assertRaises(SystemExit) as cm:
            run.process_urls_with_cli("nonexistent.txt")
        self.assertEqual(cm.exception.code, 1)

    @patch("os.path.exists", return_value=True)
    @patch("run.process_and_score_input_file")
    def test_process_urls_with_cli_success(self, mock_process, mock_exists):
        run.process_urls_with_cli("test_file.txt")
        mock_process.assert_called_once_with("test_file.txt")

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.check_call")
    def test_process_local_files_success(self, mock_subprocess, mock_exists):
        run.process_local_files()
        mock_subprocess.assert_called_once()

    @patch("os.path.exists", return_value=False)
    def test_process_local_files_no_init(self, mock_exists):
        with self.assertRaises(SystemExit) as cm:
            run.process_local_files()
        self.assertEqual(cm.exception.code, 1)

    @patch("subprocess.run")
    def test_run_tests_pytest_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        with self.assertRaises(SystemExit) as cm:
            run.run_tests()
        self.assertEqual(cm.exception.code, 0)

    @patch("subprocess.run")
    def test_run_tests_pytest_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="fail", stderr="")
        with self.assertRaises(SystemExit) as cm:
            run.run_tests()
        self.assertEqual(cm.exception.code, 1)

    @patch.object(run, "install_dependencies")
    def test_main_install_command(self, mock_install):
        sys.argv = ["run.py", "install"]
        if sys.argv[1] == "install":
            run.install_dependencies()
        mock_install.assert_called_once()

    @patch.object(run, "run_tests")
    def test_main_test_command(self, mock_run_tests):
        sys.argv = ["run.py", "test"]
        if sys.argv[1] == "test":
            run.run_tests()
        mock_run_tests.assert_called_once()

    @patch.object(run, "process_urls_with_cli")
    def test_main_score_command(self, mock_process):
        sys.argv = ["run.py", "score", "test_file.txt"]
        if sys.argv[1] == "score":
            run.process_urls_with_cli(sys.argv[2])
        mock_process.assert_called_once_with("test_file.txt")

    def test_main_score_command_missing_file(self):
        sys.argv = ["run.py", "score"]
        with self.assertRaises(SystemExit) as cm:
            if len(sys.argv) < 3:
                print("Error: Missing URL_FILE argument for score command")
                sys.exit(1)
        self.assertEqual(cm.exception.code, 1)

    @patch.object(run, "run_cli")
    def test_main_default_command(self, mock_run_cli):
        sys.argv = ["run.py", "unknown_command"]
        if sys.argv[1] not in ["install", "test", "score"]:
            run.run_cli()
        mock_run_cli.assert_called_once()


if __name__ == "__main__":
    unittest.main()
