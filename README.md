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

### Command-line
Can be run to transform values at the command-line, transforming stdin to stdout as
JSON. Pass `-d` to deserialise instead of serialise.

The following example uses [AWS CLI (`aws`)](https://aws.amazon.com/cli/) to produce
DynamoDB values in lists of objects, [`jq`](https://jqlang.github.io/jq/) to convert the
[scan](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Scan.html)
result to full DynamoDB values, and `dynamodb-serialise` to convert to native types.

```shell
aws dynamodb scan \
  --table-name my-table \
  | jq '{ L: .Items | map({ M: . }) }' \
  | python3 -m dynamodb_serialise -d
```
