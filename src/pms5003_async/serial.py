import aioserial
import contextlib
import struct
import time
import typing

from .measurement import PMS5003Measurement


class DataError(RuntimeError):
    pass


class PMS5003Serial:

    _FRAME_LENGTH = 28

    #: char 1 == 0x42, char 2 == 0x47, frame length == 0x001c (28)
    _START_SEQUENCE = b'\x42\x4d\x00\x1c'

    def __init__(self, aioserial: aioserial.AioSerial) -> None:
        self._aioserial = aioserial


    async def _read_start(self) -> bool:
        for expected in PMS5003Serial._START_SEQUENCE:
            c = ord(await self._aioserial.read_async(1))
            if c != expected:
                return False
        return True


    def _parse(frame: bytes) -> PMS5003Measurement:
        unpacked = struct.unpack(">HHHHHHHHHHHHHH", frame)
        actual_checksum = sum(PMS5003Serial._START_SEQUENCE + frame[:-2])
        expected_checksum = unpacked[13]
        if actual_checksum != expected_checksum:
            return DataError()
        # The second to last is a "reserved" field
        # The last is the "checksum" field.
        return PMS5003Measurement(*unpacked[:-2])


    async def try_read_one(self) -> typing.Optional[typing.Tuple[float, PMS5003Measurement]]:
        if not await self._read_start():
            return None
        timestamp = time.time()
        frame = await self._aioserial.read_async(PMS5003Serial._FRAME_LENGTH)
        return timestamp, PMS5003Serial._parse(frame)


    async def read_one(self) -> typing.Tuple[float, PMS5003Measurement]:
        # todo: limits on amount of bytes / time
        while True:
            item = await self.try_read_one()
            if item:
                return item

    
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


@contextlib.asynccontextmanager
async def open_pms(port='/dev/ttyAMA0', baudrate=9600):
    _aioserial = aioserial.AioSerial(port=port, baudrate=baudrate)
    yield PMS5003Serial(_aioserial)
    _aioserial.close()
