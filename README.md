# Simtest

Simtest is the thin Python service wrapper
around [pytest-simbind](https://github.com/swag-engineering/pytest-simbind?tab=readme-ov-file#using-api)'s API. Service
exposes 2 gRPC endpoints:

```protobuf
service Simtest {
  rpc InstallWheelPackage (InstallWheelPackageRequest) returns (Empty);
  rpc StartTests (StartTestsRequest) returns (stream FunctionUpdate);
}
```

For full list of types/messages please, explore
_[simtest.proto](https://github.com/swag-engineering/simtest/blob/master/simtest.proto)_.

### Installing packages

_InstallWheelPackage_ allows the installation of Python packages required to run tests,
e.g. [Simbind model](https://github.com/swag-engineering/simbind-cli). _package_bytes_ parameter in
_InstallWheelPackageRequest_ should be a zip archive containing the wheel package and all its dependencies in bytes
format. For more details, please refer to
this [code snippet](https://github.com/swag-engineering/simtest/blob/master/tests/integration/conftest.py#L64).

### Executing tests

_StartTests_ executes tests and sends collected data, logs and reports via
stream.  
[pytest-simbind](https://github.com/swag-engineering/pytest-simbind?tab=readme-ov-file#using-api)'s API requires
user to provide
_[selector callback](https://github.com/swag-engineering/pytest-simbind/blob/master/pytest_simbind/SimbindCollector.py#L21)_
that services two purposes:

- select tests to run
- tag each test with specific id to identify later collected data

In same manner _functions_ parameter in _StartTestsRequest_ serves to select tests for execution and assign a unique
_id_ to each test, facilitating later identification of collected data:

```protobuf
message TestFunction {
  string id = 1;
  string node_id = 2;
}
```

- _node_id_ here is _pytest_'s _nodeid_ that essentially looks like _outer_package/inner_package/module.py::test_name_.
- _id_ is the identifier that _pytest_ will use to tag data associated with a specified test. This might be beneficial
  for scenarios where you plan to store test data in a database and wish to avoid performing additional translation upon
  the arrival of the data. Otherwise, you can make _id_ equal to _node_id_. It is the user's responsibility to ensure
  the uniqueness of the provided _id_'s!

[Tests](https://github.com/swag-engineering/simtest/blob/master/tests/integration/data_collection_test.py#L241) can
serve as a valuable example for reference!

## Usage and integrations

The Simtest container is intended for one-time use: it should be launched, get dependencies installed, execute a single
test run, and then be shut down. Since no cleanup process is implemented, any subsequent test executions could
potentially interfere with each other.

Service is designed in a way to operate in isolated manner. Therefore, if you have concerns about the trustworthiness of
the tests or data, such as those written by a third party, we strongly recommend implementing strict ingress and egress
network policies!