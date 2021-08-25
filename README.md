# DynamoDB value serialisation and deserialisation
Convert values from AWS DynamoDB to native Python types.

Makes more sensible decisions about numbers and binary values, at the cost of
floating-point precision. Very lightweight.

## Installation
```shell
pip install dynamodb-serialise
```

## Usage
```python
import dynamodb_serialise

dynamodb_serialise.deserialise(
    {"M": {"foo": {"N": "42"}, "bar": {"B": "c3BhbQ=="}}}
)
# {'foo': 42, 'bar': b'spam'}

dynamodb_serialise.serialise(
    {'foo': 42, 'bar': b'spam'}, bytes_to_base64=True
)
# {"M": {"foo": {"N": "42"}, "bar": {"B": "c3BhbQ=="}}}
```
