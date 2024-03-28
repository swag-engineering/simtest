import uuid

import pytest

from simtest import proto


@pytest.fixture(scope="function", autouse=True)
async def preinstall_model(
        example_model_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    request = proto.grpc.InstallWheelPackageRequest("model", example_model_bytes, True)
    await simtest_client.install_wheel_package(request)


async def test_no_selection(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[]
    )
    async for _ in simtest_client.start_tests(request):
        assert False, "No messages expected"


async def test_1_1_1_non_zero_input_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test_id,
                node_id="package1/module_1_1_test.py::test_1_1_1_non_zero_input"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert len(test_data) == 2

    assert test_data[0].test_id == test_id
    assert test_data[0].progress == proto.grpc.FunctionProgressEnum.RUNNING
    assert test_data[0].data.timestamp == 0
    assert any([val != 0 for val in test_data[0].data.inputs.values()])
    assert test_data[0].status is None

    assert test_data[1].test_id == test_id
    assert test_data[1].progress == proto.grpc.FunctionProgressEnum.FINISHED
    assert test_data[1].status.state == proto.grpc.FunctionStateEnum.SUCCEED
    assert test_data[1].data is None


async def test_1_1_2_ten_steps_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test_id,
                node_id="package1/module_1_1_test.py::test_1_1_2_ten_steps"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert len(test_data) == 12

    assert test_data[0].test_id == test_id
    assert test_data[0].progress == proto.grpc.FunctionProgressEnum.RUNNING
    assert test_data[0].data.timestamp == 0
    assert any([val != 0 for val in test_data[0].data.inputs.values()])
    assert test_data[0].status is None

    assert len([update for update in test_data if update.data and update.data.timestamp == 0]) == 1

    assert test_data[11].test_id == test_id
    assert test_data[11].progress == proto.grpc.FunctionProgressEnum.FINISHED
    assert test_data[11].status.state == proto.grpc.FunctionStateEnum.SUCCEED
    assert test_data[11].data is None


async def test_module_1_1_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test1_id = str(uuid.uuid4())
    test2_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test1_id,
                node_id="package1/module_1_1_test.py::test_1_1_1_non_zero_input"
            ),
            proto.grpc.TestFunction(
                id=test2_id,
                node_id="package1/module_1_1_test.py::test_1_1_2_ten_steps"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert len(test_data) == 14

    test1_data = [data for data in test_data if data.test_id == test1_id]
    test2_data = [data for data in test_data if data.test_id == test2_id]

    assert len(test1_data) == 2
    assert len(test2_data) == 12
    assert len([
        update for update in test1_data if
        update.progress == proto.grpc.FunctionProgressEnum.FINISHED and
        update.status.state == proto.grpc.FunctionStateEnum.SUCCEED
    ]) == 1
    assert len([
        update for update in test2_data if
        update.progress == proto.grpc.FunctionProgressEnum.FINISHED and
        update.status.state == proto.grpc.FunctionStateEnum.SUCCEED
    ]) == 1


async def test_2_1_1_single_log_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test_id,
                node_id="package2/module_2_1_test.py::test_2_1_1_single_log"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert len(test_data) == 2
    assert len(test_data[0].data.log_messages) == 1


async def test_2_1_2_ten_logs_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test_id,
                node_id="package2/module_2_1_test.py::test_2_1_2_ten_logs"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert len(test_data) == 12
    for idx in range(10):
        assert len(test_data[idx].data.log_messages) == 1
    assert len(test_data[10].data.log_messages) == 0
    assert test_data[11].data is None


async def test_21_1_1_realistic_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test_id,
                node_id="package2/package21/module_21_1_test.py::test_21_1_1_realistic"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert test_data[-2].data.timestamp >= 0.1
    assert test_data[-1].progress == proto.grpc.FunctionProgressEnum.FINISHED
    assert test_data[-1].status.state == proto.grpc.FunctionStateEnum.FAILED
    assert test_data[-1].data is None
    assert test_data[-1].status.internal_error is None
    assert test_data[-1].status.fail_details is not None
    assert test_data[-1].status.fail_details.line_number == 15
    assert test_data[-1].status.fail_details.file_location == "package2/package21/module_21_1_test.py"
    assert test_data[-1].status.fail_details.text == "Something went wrong"


async def test_21_1_2_exception(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    test_id = str(uuid.uuid4())
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=test_id,
                node_id="package2/package21/module_21_1_test.py::test_21_1_2_exception"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert test_data[-1].progress == proto.grpc.FunctionProgressEnum.FINISHED
    assert test_data[-1].status.state == proto.grpc.FunctionStateEnum.FAILED
    assert test_data[-1].data is None
    assert test_data[-1].status.internal_error is None
    assert test_data[-1].status.fail_details is not None
    assert test_data[-1].status.fail_details.line_number == 20
    assert test_data[-1].status.fail_details.file_location == "package2/package21/module_21_1_test.py"
    assert test_data[-1].status.fail_details.text == "Something went wrong"


async def test_all_selected(
        example_tests_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    request = proto.grpc.StartTestsRequest(
        tests_bytes=example_tests_bytes,
        functions=[
            proto.grpc.TestFunction(
                id=str(uuid.uuid4()),
                node_id="package1/module_1_1_test.py::test_1_1_1_non_zero_input"
            ),
            proto.grpc.TestFunction(
                id=str(uuid.uuid4()),
                node_id="package1/module_1_1_test.py::test_1_1_2_ten_steps"
            ),
            proto.grpc.TestFunction(
                id=str(uuid.uuid4()),
                node_id="package2/module_2_1_test.py::test_2_1_1_single_log"
            ),
            proto.grpc.TestFunction(
                id=str(uuid.uuid4()),
                node_id="package2/module_2_1_test.py::test_2_1_2_ten_logs"
            ),
            proto.grpc.TestFunction(
                id=str(uuid.uuid4()),
                node_id="package2/package21/module_21_1_test.py::test_21_1_1_realistic"
            ),
            proto.grpc.TestFunction(
                id=str(uuid.uuid4()),
                node_id="package2/package21/module_21_1_test.py::test_21_1_2_exception"
            )
        ]
    )
    test_data = []
    async for msg in simtest_client.start_tests(request):
        test_data.append(msg)

    assert len(set([update.test_id for update in test_data])) == 6
    assert len([update for update in test_data if update.progress == proto.grpc.FunctionProgressEnum.FINISHED]) == 6
    assert len([
        update for update in test_data if
        update.progress == proto.grpc.FunctionProgressEnum.FINISHED and
        update.status.state == proto.grpc.FunctionStateEnum.FAILED
    ]) == 2
