# Contribution guide
Thanks for wanting to help out!

## Development environment set-up
Create a new `setup.py`:
```python
from setuptools import setup

setup()
```

Install package
```shell
pip install -e .
```

Install package testing requirements
```shell
pip install -r tests/requirements.txt black
```

## Testing
Run the test suite
```shell
pytest -vvra
```

Run linting
```shell
black --check src
```

## Submitting changes
Make sure the above test is successful, then make a pull-request on GitHub. 
