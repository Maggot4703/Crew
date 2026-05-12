# flake8: noqa: E402
import unittest
from argparse import Namespace

# Import the CLI command registry and handlers
glob = globals()
if "run_cli" not in glob:
    from cli import COMMAND_REGISTRY, run_cli
else:
    run_cli = glob["run_cli"]
    COMMAND_REGISTRY = glob["COMMAND_REGISTRY"]


def dummy_logger(*args, **kwargs):
    class Dummy:
        def info(self, *a, **k):
            pass

        def error(self, *a, **k):
            pass

        def warning(self, *a, **k):
            pass

    return Dummy()


class TestCLIHandlers(unittest.TestCase):
    def test_read_csv_file_not_found(self):
        args = Namespace(command="read-csv", csv_path="/tmp/does_not_exist.csv")
        result = run_cli(args)
        self.assertEqual(result, 1)

    def test_read_excel_file_not_found(self):
        args = Namespace(
            command="read-excel", excel_path="/tmp/does_not_exist.xlsx", sheet=None
        )
        result = run_cli(args)
        self.assertEqual(result, 1)

    def test_crop_csv_file_not_found(self):
        args = Namespace(
            command="crop-csv",
            image_path="/tmp/does_not_exist.png",
            annotations_csv="/tmp/does_not_exist.csv",
            output_dir="/tmp/out",
            output_format=None,
            quality=95,
        )
        result = run_cli(args)
        self.assertEqual(result, 1)

    def test_unknown_command(self):
        args = Namespace(command="not-a-command")
        result = run_cli(args)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
