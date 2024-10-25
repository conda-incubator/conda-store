# conda-store server

A multi-tenant server for managing conda environments.
See the [documentation](https://conda.store/) for more information.

## Running tests

### Run tests with pytest
```
# ignoring integration tests
$ python -m pytest -m "not extended_prefix and not user_journey" tests/

# ignoring long running tests
$ python -m pytest -m "not extended_prefix and not user_journey and not long_running_test" tests/
```

### Run tests with code coverage
Ensure you have pytest-cov install
```
$ pip install pytest-cov
```

Run tests
```
$ python -m pytest -m "not extended_prefix and not user_journey" --cov=conda_store_server tests/
```

Check coverage report
```
$ coverage report
```
