import os
import sys
import asyncio
import logging
import zipfile
import tempfile
from typing import AsyncIterator

from pytest_simbind import SimbindCollector, dto as simbind_dto

from simtest import proto


_dto2proto_progress: dict[simbind_dto.TestProgressEnum, proto.grpc.FunctionProgressEnum] = {
    simbind_dto.TestProgressEnum.IDLE: proto.grpc.FunctionProgressEnum.IDLE,
    simbind_dto.TestProgressEnum.RUNNING: proto.grpc.FunctionProgressEnum.RUNNING,
    simbind_dto.TestProgressEnum.FINISHED: proto.grpc.FunctionProgressEnum.FINISHED
}

_dto2proto_state: dict[simbind_dto.TestStateEnum, proto.grpc.FunctionStateEnum] = {
    simbind_dto.TestStateEnum.SUCCEED: proto.grpc.FunctionStateEnum.SUCCEED,
    simbind_dto.TestStateEnum.FAILED: proto.grpc.FunctionStateEnum.FAILED,
    simbind_dto.TestStateEnum.TERMINATED: proto.grpc.FunctionStateEnum.TERMINATED
}

_dto2proto_log_level: dict[simbind_dto.LogLevelEnum, proto.grpc.LogLevelEnum] = {
    simbind_dto.LogLevelEnum.DEBUG: proto.grpc.LogLevelEnum.DEBUG,
    simbind_dto.LogLevelEnum.INFO: proto.grpc.LogLevelEnum.INFO,
    simbind_dto.LogLevelEnum.WARNING: proto.grpc.LogLevelEnum.WARNING,
    simbind_dto.LogLevelEnum.ERROR: proto.grpc.LogLevelEnum.ERROR,
    simbind_dto.LogLevelEnum.CRITICAL: proto.grpc.LogLevelEnum.CRITICAL
}


class SimtestService(proto.grpc.SimtestBase):
    async def start_tests(self, request: proto.grpc.StartTestsRequest) -> AsyncIterator[proto.grpc.FunctionUpdate]:
        tests_tmp_dir = tempfile.TemporaryDirectory()
        tests_root_dir = unzip_bytes(tests_tmp_dir.name, request.tests_bytes)
        classifier_map = {func.node_id: func.id for func in request.functions}

        collector = SimbindCollector(
            tests_root_dir,
            lambda test_case: classifier_map[test_case.node_id] if test_case.node_id in classifier_map else None
        )
        async for msg in collector.start():
            yield proto.grpc.FunctionUpdate(
                test_id=msg.test_id,
                progress=_dto2proto_progress[msg.progress],
                data=proto.grpc.TestDataRecord(
                    timestamp=msg.data.timestamp,
                    inputs=msg.data.inputs,
                    outputs=msg.data.outputs,
                    log_messages=[
                        proto.grpc.LogMessage(
                            log_level=_dto2proto_log_level[log.log_level],
                            text=log.text,
                            line_number=log.line_number,
                            file_location=log.file_location
                        ) for log in msg.data.log_messages
                    ]
                ) if msg.data is not None else None,
                status=proto.grpc.TestStatus(
                    state=_dto2proto_state[msg.status.state],
                    fail_details=proto.grpc.FailDetails(
                        exc_type=msg.status.fail_details.exc_type,
                        text=msg.status.fail_details.text,
                        line_number=msg.status.fail_details.line_number,
                        file_location=msg.status.fail_details.file_location
                    ) if msg.status.fail_details is not None else None,
                    internal_error=msg.status.internal_error
                ) if msg.status is not None else None
            )

    async def install_wheel_package(self, request: proto.grpc.InstallWheelPackageRequest) -> proto.grpc.Empty:
        package_tmp_dir = tempfile.TemporaryDirectory()
        package_root_dir = unzip_bytes(package_tmp_dir.name, request.package_bytes)
        await install_package(package_root_dir, request.package_name, request.force_reinstall)
        return proto.grpc.Empty()


def unzip_bytes(out_dir, zip_bytes):
    tmp_folder = tempfile.TemporaryDirectory()
    archive_path = os.path.join(tmp_folder.name, "archive.zip")
    with open(archive_path, "wb") as file_obj:
        file_obj.write(zip_bytes)
    with zipfile.ZipFile(archive_path, 'r') as zip_obj:
        common_root = os.path.commonpath(zip_obj.namelist())
        zip_obj.extractall(out_dir)
    tmp_folder.cleanup()
    return os.path.join(out_dir, common_root)


async def install_package(package_dir: str, package_name: str, force_reinstall: bool) -> None:
    force_str = "--force-reinstall" if force_reinstall else ""
    process = await asyncio.create_subprocess_shell(
        f"{sys.executable} -m pip install --no-index {force_str} --find-links={package_dir} {package_name}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    logging.info(stdout)
    if stderr:
        logging.error(stderr)
    if process.returncode:
        raise KeyError(f"During installation of {package_name} got:\n{stderr.decode('utf-8')}")
