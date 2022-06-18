import aioserial
import asyncio
import dataclasses
import datetime
import json
import struct
import sys
import time

from contextlib import asynccontextmanager


__version__ = '0.0.1.dev2'


def _pretty_timestamp(timestamp: float) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.%f%zZ')


@dataclasses.dataclass
class PMS5003Measurement:
    """
    PMS5003 air quality sensor measurement

    See http://www.aqmd.gov/docs/default-source/aq-spec/resources-page/plantower-pms5003-manual_v2-3.pdf
    """

    #: PM1.0 concentration unit μg/m³ (CF=1, standard particle)
    pm_1: int

    #: PM2.5 concentration unit μg/m³ (CF=1, standard particle)
    pm_2_5: int

    #: PM10 concentration unit μg/m³ (CF=1, standard particle)
    pm_10: int

    #: PM1.0 concentration unit μg/m³ (under atmospheric environment)
    pm_1_atmosphere: int

    #: PM2.5 concentration unit μg/m³ (under atmospheric environment)
    pm_2_5_atmosphere: int

    #: PM10 concentration unit μg/m³ (under atmospheric environment)
    pm_10_atmosphere: int

    #: Number of particles with diameter beyond 0.3 μm in 0.1 L of air
    p_0_3: int

    #: Number of particles with diameter beyond 0.5 μm in 0.1 L of air
    p_0_5: int

    #: Number of particles with diameter beyond 1.0 μm in 0.1 L of air
    p_1_0: int

    #: Number of particles with diameter beyond 2.5 μm in 0.1 L of air
    p_2_5: int

    #: Number of particles with diameter beyond 5.0 μm in 0.1 L of air
    p_5_0: int

    #: Number of particles with diameter beyond 10 μm in 0.1 L of air
    p_10: int

    #: Reserved
    reserved: int


    def csv(self, timestamp=None) -> str:
        """Output the measurement as a CSV line"""
        return ",".join(([_pretty_timestamp(timestamp)] if timestamp else []) + [str(x) for x in dataclasses.astuple(self)])


    def json(self, timestamp=None) -> str:
        """Output the measurement as a JSON line"""
        timestamp_dict = {"timestamp": _pretty_timestamp(timestamp)} if timestamp else {}
        measurement_dict = dataclasses.asdict(self)
        return json.dumps({**timestamp_dict, **measurement_dict})


class DataError(RuntimeError):
    pass


def parse(data: bytes) -> PMS5003Measurement:
    if len(data) != 32:
        raise DataError("Expected 32 bytes")
    # todo first 4 bytes
    unpacked = struct.unpack(">HHHHHHHHHHHHHH", data[4:])
    actual_checksum = sum(data[:-2])
    expected_checksum = unpacked[13]
    if actual_checksum != expected_checksum:
        raise DataError()
    return PMS5003Measurement(*unpacked[:-1])


class PMS5003Serial:
    def __init__(self, aioserial: aioserial.AioSerial) -> None:
        self._aioserial = aioserial


    async def read_one(self):
        """Returns a tuple of the current timestamp and the PMS5003 measurement"""
        data = await self._aioserial.read_async(32)
        timestamp = time.time()
        return timestamp, parse(data)


    async def read(
        self,
        dedupe: bool = True,
        warmup: float = 30.0):
        # todo: document why dedup may be important (active mode oversampling, see docs)
        # todo: document warmup (suggested 30s warmup, see docs)
        previous = None
        if warmup > 0:
            start_time = time.time()
            warmup_time = start_time + warmup 
            ts = start_time
            while ts < warmup_time:
                ts, current = await self.read_one()
                previous = current
        while True:
            ts, current = await self.read_one()
            if dedupe and current == previous:
                continue
            previous = current
            yield ts, current


    async def print_csv(self, file=sys.stdout):
        async for _, current in self.read(dedupe=True, warmup=30.0):
            print(current.csv(), file=file)


@asynccontextmanager
async def open_pms(port='/dev/ttyAMA0', baudrate=9600):
    _aioserial = aioserial.AioSerial(port=port, baudrate=baudrate)
    yield PMS5003Serial(_aioserial)
    _aioserial.close()


async def write_csv(port='/dev/ttyAMA0', with_header=True, with_timestamp=True, dedupe=True, warmup=30.0, file=sys.stdout):
    async with open_pms(port=port) as pms:
        if with_header:
            print(f"{'timestamp,' if with_timestamp else ''}pm_1,pm_2_5,pm_10,pm_1_atmosphere,pm_2_5_atmosphere,pm_10_atmosphere,p_0_1,p_0_5,p_1_0,p_2_5,p_5_0,p_10,reserved", file=file)
        async for timestamp, current in pms.read(dedupe=dedupe, warmup=warmup):
            print(f"{current.csv(timestamp if with_timestamp else None)}", file=file)


async def write_json(port='/dev/ttyAMA0', with_timestamp=True, dedupe=True, warmup=30.0, file=sys.stdout):
    async with open_pms(port=port) as pms:
        async for timestamp, current in pms.read(dedupe=dedupe, warmup=warmup):
            print(f"{current.json(timestamp if with_timestamp else None)}", file=file)


def write_csv_main():
    # TODO: argparse CLI
    print('Writing csv. May be short warmup delay...', file=sys.stderr)
    asyncio.run(write_csv())


def write_json_main():
    # TODO: argparse CLI
    print("Writing json. May be short warmup delay...", file=sys.stderr)
    asyncio.run(write_json())


# TODO: single entrypoint, single main