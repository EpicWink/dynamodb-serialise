"""Test ``dynamodb_serialise``."""

import io
import sys
import json
import unittest.mock

import pytest

import dynamodb_serialise


class DynamoDBSetEqual(dict):
    def __init__(self, serialised: dict) -> None:
        super().__init__(serialised)
        (self._descriptor,) = serialised
        self._elements = set(serialised[self._descriptor])

    def __eq__(self, other):
        return (
            set(other) == {self._descriptor}
            and set(other[self._descriptor]) == self._elements
        )


cases = [
    (
        "small_example",
        {"M": {"foo": {"N": "42"}, "bar": {"S": "spam"}}},
        {"foo": 42, "bar": "spam"},
        True,
        None,
    ),
    (
        "full_example",
        {
            "M": {
                "foo": {"N": "42"},
                "bar": {"B": "c3BhbQ=="},
                "baz": {
                    "L": [
                        {"S": "eggs"},
                        DynamoDBSetEqual({"SS": ["spam", "eggs"]}),
                        {"N": "4.2"},
                    ],
                },
                "qux": {
                    "M": {
                        "foo": {"NS": ["42"]},
                        "bar": {"BS": ["ZWdncw=="]},
                        "baz": {"L": []},
                        "qux": {"M": {}},
                    },
                },
                "ess": {"SS": []},
                "yes": {"BOOL": True},
                "no": {"BOOL": False},
                "none": {"NULL": True},
            },
        },
        {
            "foo": 42,
            "bar": b"spam",
            "baz": ["eggs", {"spam", "eggs"}, 4.2],
            "qux": {"foo": {42}, "bar": {b"eggs"}, "baz": [], "qux": {}},
            "ess": set(),
            "yes": True,
            "no": False,
            "none": None,
        },
        True,
        "SS",
    ),
    ("empty_map", {"M": {}}, {}, None, None),
    ("small_map", {"M": {"foo": {"N": "42"}}}, {"foo": 42}, None, None),
    ("empty_list", {"L": []}, [], None, None),
    ("small_list", {"L": [{"N": "42"}]}, [42], None, None),
    ("empty_string_set_default", {"SS": []}, set(), None, None),
    ("empty_string_set", {"SS": []}, set(), None, "SS"),
    ("small_string_set", {"SS": ["spam"]}, {"spam"}, None, None),
    ("empty_number_set", {"NS": []}, set(), None, "NS"),
    ("small_number_set", {"NS": ["42"]}, {42}, None, None),
    ("empty_binary_set", {"BS": []}, set(), None, "BS"),
    ("small_binary_set", {"BS": ["c3BhbQ=="]}, {b"spam"}, True, None),
    ("integer", {"N": "42"}, 42, None, None),
    ("floating", {"N": "4.2"}, 4.2, None, None),
    ("binary_bytes_default", {"B": b"spam"}, b"spam", None, None),
    ("binary_base64", {"B": "c3BhbQ=="}, b"spam", True, None),
    ("binary_bytes", {"B": b"spam"}, b"spam", False, None),
    ("string", {"S": "spam"}, "spam", None, None),
    ("true", {"BOOL": True}, True, None, None),
    ("false", {"BOOL": False}, False, None, None),
    ("null", {"NULL": True}, None, None, None),
]


@pytest.mark.parametrize(
    ("serialised", "expected"), [pytest.param(*c[1:3], id=c[0]) for c in cases]
)
def test_deserialise(serialised, expected) -> None:
    assert dynamodb_serialise.deserialise(serialised) == expected


@pytest.mark.parametrize(("serialised", "message"), [
    pytest.param({}, "Invalid DynamoDB value", id="empty"),
    pytest.param({"N": "42", "S": "spam"}, "Invalid DynamoDB value", id="multiple"),
    pytest.param({"D": "4.2"}, "Unknown DynamoDB type", id="unknown"),
])  # fmt: skip
def test_deserialise_raises(serialised, message: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        dynamodb_serialise.deserialise(serialised)
    assert message in str(exc_info.value)


@pytest.mark.parametrize(
    ("expected", "deserialised", "bytes_to_base64", "empty_set_type"),
    [pytest.param(*c[1:], id=c[0]) for c in cases],
)
def test_serialise(expected, deserialised, bytes_to_base64, empty_set_type) -> None:
    kw = {}
    if bytes_to_base64 is not None:
        kw["bytes_to_base64"] = bytes_to_base64
    if empty_set_type is not None:
        kw["empty_set_type"] = empty_set_type
    assert dynamodb_serialise.serialise(deserialised, **kw) == expected


def test_serialise_decimal() -> None:
    import decimal

    assert dynamodb_serialise.serialise(decimal.Decimal("4.2")) == {"N": "4.2"}


def test_serialise_collections() -> None:
    import collections

    assert dynamodb_serialise.serialise(collections.UserList([42])) == {
        "L": [{"N": "42"}],
    }
    assert dynamodb_serialise.serialise(collections.OrderedDict({"foo": 42})) == {
        "M": {"foo": {"N": "42"}},
    }
    assert dynamodb_serialise.serialise(collections.UserDict({"foo": 42})) == {
        "M": {"foo": {"N": "42"}},
    }


def test_serialise_fallback() -> None:
    def fallback(o):
        if o is obj:
            return {"M": {"$obj": {"NULL": True}}}
        raise exc

    exc = ValueError("foo")
    obj = object()
    assert dynamodb_serialise.serialise(obj, fallback=fallback) == {
        "M": {"$obj": {"NULL": True}},
    }

    with pytest.raises(ValueError) as exc_info:
        dynamodb_serialise.serialise(object(), fallback=fallback)
    assert exc_info.value is exc


@pytest.mark.parametrize(("deserialised", "message"), [
    pytest.param(object(), "Unhandled type", id="unknown"),
    pytest.param({int}, "Unhandled type for set elements", id="unknown_set"),
    pytest.param(
        {42, "spam", b"eggs"},
        "Set elements must be of only one type",
        id="multiple_set",
    ),
])  # fmt: skip
def test_serialise_raises(deserialised, message: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        dynamodb_serialise.serialise(deserialised)
    assert message in str(exc_info.value)


@pytest.mark.parametrize(("deserialise", "input_data", "expected_output_data"), [
    pytest.param(
        True,
        cases[0][1],
        cases[0][2],
        id="deserialise",
    ),
    pytest.param(
        False,
        cases[0][2],
        cases[0][1],
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
