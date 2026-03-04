from pathlib import Path
from crawler.__main__ import parse_args
import pytest


@pytest.mark.parametrize(
    "args,expected_input_file,expected_output_file",
    [
        [["-i", "input_file.txt", "-o", "output_dir"], "input_file.txt", "output_dir"],
    ],
)
def test_parse_args(
    args: list[str],
    expected_input_file: Path,
    expected_output_file: Path,
) -> None:
    parsed_args = parse_args(args)
    assert Path(expected_input_file) == parsed_args.input_file
    assert Path(expected_output_file) == parsed_args.output_dir
