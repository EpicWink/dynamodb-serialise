"""Test ``dynamodb_serialise``."""

# TODO: more comprehensive testing

import io
import sys
import json
import unittest.mock

import pytest

import dynamodb_serialise


def test_deserialisation():
    assert dynamodb_serialise.deserialise(
        {"M": {"foo": {"N": "42"}, "bar": {"B": "c3BhbQ=="}}}
    ) == {'foo': 42, 'bar': b'spam'}


def test_serialisation():
    assert dynamodb_serialise.serialise(
        {'foo': 42, 'bar': b'spam'}, bytes_to_base64=True
    ) == {"M": {"foo": {"N": "42"}, "bar": {"B": "c3BhbQ=="}}}


@pytest.mark.parametrize(("deserialise", "input_data", "expected_output_data"), [
    pytest.param(
        True,
        {"M": {"foo": {"N": "42"}, "bar": {"S": "spam"}}},
        {"foo": 42, "bar": "spam"},
        id="deserialise",
    ),
    pytest.param(
        False,
        {"foo": 42, "bar": "spam"},
        {"M": {"foo": {"N": "42"}, "bar": {"S": "spam"}}},
        id="serialise",
    ),
])  # fmt: skip
def test_main(
    deserialise: bool,
    input_data: dict,
    expected_output_data: dict,
    capsys,
) -> None:
    new_argv = ["dynamodb_serialise.py"]
    if deserialise:
        new_argv += ["-d"]
    argv_patch = unittest.mock.patch.object(sys, "argv", new_argv)

    input_json = json.dumps(input_data)
    new_stdin = io.StringIO(input_json)
    stdin_patch = unittest.mock.patch.object(sys, "stdin", new_stdin)

    with argv_patch, stdin_patch:
        dynamodb_serialise.main()

    captured = capsys.readouterr()
    result_output_data = json.loads(captured.out)
    assert result_output_data == expected_output_data
