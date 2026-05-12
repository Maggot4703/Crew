import os
import sys
from unittest import mock


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cli as cli_mod

# Test CLI entry points by patching sys.argv and intercepting file I/O


def run_cli_with_args(args):
    sys_argv = ["Crew.py"] + args
    with mock.patch.object(sys, "argv", sys_argv):
        try:
            return cli_mod.run_cli(cli_mod.create_cli_parser().parse_args())
        except SystemExit as e:
            return e.code


def test_cli_help(capsys):
    code = run_cli_with_args(["--help"])
    out, err = capsys.readouterr()
    assert code == 0 or code == 1
    assert "usage" in out.lower()


def test_cli_invalid_command(capsys):
    code = run_cli_with_args(["not-a-command"])
    out, err = capsys.readouterr()
    # argparse returns exit code 2 for invalid commands
    assert code == 1 or code == 2
    # Custom error output is printed to stderr
    assert "usage" in err.lower() or "error" in err.lower()


# Add more tests for each subcommand, patching file I/O as needed
# Example for grid-image (does not actually write files)
def test_cli_grid_image(monkeypatch, tmp_path, capsys):
    from unittest.mock import MagicMock, patch

    dummy_image = tmp_path / "dummy.png"
    output_image = tmp_path / "output.png"

    # Mock PIL.Image.open to return a mock image
    mock_image = MagicMock()
    mock_image.save = MagicMock()

    # Create dummy image file (doesn't need to be valid)
    dummy_image.write_bytes(b"\x89PNG\r\n\x1a\n")

    # Patch PIL.Image.open and overlay_grid
    with patch("PIL.Image.open", return_value=mock_image), patch(
        "cli.overlay_grid", return_value=mock_image
    ):
        parser = cli_mod.create_cli_parser()
        args = parser.parse_args(
            [
                "grid-image",
                "--image-path",
                str(dummy_image),
                "--output-path",
                str(output_image),
            ]
        )
        code = cli_mod.run_cli(args)

        assert code == 0, f"Exit code {code}"
        mock_image.save.assert_called_once()


# More tests for other subcommands and error cases can be added similarly
