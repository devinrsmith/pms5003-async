import aioserial
import asyncio
import dataclasses
import json
import struct
import time


__version__ = '0.0.1.dev0'


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

    def csv(self) -> str:
        """Output the measurement as a CSV line"""
        return ",".join([str(x) for x in dataclasses.astuple(self)])
        
    def json(self) -> str:
        """Output the measurement as a JSON line"""
        return json.dumps(dataclasses.asdict(self))


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


async def read_one(aioserial_instance: aioserial.AioSerial):
    """Returns a tuple of the current timestamp and the PMS5003 measurement"""
    data = await aioserial_instance.read_async(32)
    timestamp = time.time()
    return timestamp, parse(data)


async def read(
    aioserial_instance: aioserial.AioSerial,
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
            ts, current = await read_one(aioserial_instance)
            previous = current
    while True:
        ts, current = await read_one(aioserial_instance)
        if dedupe and current == previous:
            continue
        previous = current
        yield ts, current


async def print(aioserial_instance: aioserial.AioSerial):
    async for _, current in read(aioserial_instance, dedupe=True, warmup=30.0):
        print(current.json())
    

aioserial_instance = aioserial.AioSerial(port='/dev/ttyAMA0', baudrate=9600)
asyncio.run(print(aioserial_instance))
