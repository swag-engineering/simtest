import asyncio
import os
import random
import shutil
import string
import tempfile

import pytest
from grpclib.client import Channel

from simtest import proto


@pytest.fixture(scope="function")
def simtest_client() -> proto.grpc.SimtestStub:
    channel = Channel(host="127.0.0.1", port=50051)
    return proto.grpc.SimtestStub(channel)


def dir_to_zip_bytes(dir_path):
    tmp_dir = tempfile.TemporaryDirectory()
    filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    zip_name = shutil.make_archive(os.path.join(tmp_dir.name, filename), 'zip', root_dir=dir_path)
    with open(zip_name, 'rb') as file_obj:
        return file_obj.read()


@pytest.fixture(scope="session")
def tests_root():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture(scope="session")
def assets_path(tests_root):
    return os.path.join(tests_root, "assets")


@pytest.fixture(scope="session")
def example_tests_path(assets_path: str):
    return os.path.join(assets_path, "example_tests")


@pytest.fixture(scope="session")
def sil_model_dir_path(assets_path: str):
    return os.path.join(assets_path, "example_model")


@pytest.fixture(scope="session")
def example_model_bytes(sil_model_dir_path) -> bytes:
    return dir_to_zip_bytes(sil_model_dir_path)


@pytest.fixture(scope="session")
def example_tests_bytes(example_tests_path) -> bytes:
    return dir_to_zip_bytes(example_tests_path)


@pytest.fixture
def package_name(request) -> str:
    return request.param


@pytest.fixture
async def package_bytes(package_name) -> bytes:
    with tempfile.TemporaryDirectory() as tmp_dir:
        process = await asyncio.create_subprocess_shell(
            f"pip download {package_name} -d {tmp_dir}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        assert process.returncode == 0, stdout + b"\n" + stderr
        return dir_to_zip_bytes(tmp_dir)

