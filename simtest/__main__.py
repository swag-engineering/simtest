import logging
import asyncio

from grpclib.server import Server
from grpclib.health.service import Health
from grpclib.reflection.service import ServerReflection

from simtest.SimtestService import SimtestService


async def main():
    services = [SimtestService(), Health()]
    services = ServerReflection.extend(services)
    server = Server(services)
    await server.start("0.0.0.0", 50051)
    await server.wait_closed()

if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    logging.getLogger("hpack").setLevel(logging.WARNING)

    logging.info("Starting SimtestController service")

    asyncio.run(main())
