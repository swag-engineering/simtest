import grpclib
import pytest

from simtest import proto


@pytest.mark.parametrize("package_name", ["beautifulsoup4", "clifashion", "pyella"], indirect=True)
async def test_install_valid_packages(
        package_name: str,
        package_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    request = proto.grpc.InstallWheelPackageRequest(package_name, package_bytes, True)
    await simtest_client.install_wheel_package(request)


@pytest.mark.parametrize("package_name", ["beautifulsoup4"], indirect=True)
async def test_install_invalid_packages(
        package_name: str,
        package_bytes: bytes,
        simtest_client: proto.grpc.SimtestStub
):
    request = proto.grpc.InstallWheelPackageRequest("flask", package_bytes, True)
    with pytest.raises(grpclib.GRPCError) as exc_info:
        await simtest_client.install_wheel_package(request)
        assert exc_info.value.status == grpclib.const.Status.NOT_FOUND
