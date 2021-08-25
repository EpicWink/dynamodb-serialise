"""Test ``dynamodb_serialise``."""

# TODO: more comprehensive testing

import dynamodb_serialise


def test_deserialisation():
    assert dynamodb_serialise.deserialise(
        {"M": {"foo": {"N": "42"}, "bar": {"B": "c3BhbQ=="}}}
    ) == {'foo': 42, 'bar': b'spam'}


def test_serialisation():
    assert dynamodb_serialise.serialise(
        {'foo': 42, 'bar': b'spam'}, bytes_to_base64=True
    ) == {"M": {"foo": {"N": "42"}, "bar": {"B": "c3BhbQ=="}}}
