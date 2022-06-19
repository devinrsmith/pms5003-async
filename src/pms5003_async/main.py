import aiofiles
import asyncio
import contextlib
import dataclasses
import os
import simple_parsing
import sys
import typing

from .serial import open_pms
from .measurement import PMS5003Measurement


# todo: how to share options
class Options:
    pass


@dataclasses.dataclass
class CSVOptions(Options):
    port: str = '/dev/ttyAMA0'
    with_timestamp: bool = True
    dedup: bool = True
    warmup: float = 30.0
    file: str = '/dev/stdout'
    with_header: bool = True


@dataclasses.dataclass
class JSONOptions(Options):
    port: str = '/dev/ttyAMA0'
    with_timestamp: bool = True
    dedup: bool = True
    warmup: float = 30.0
    file: str = '/dev/stdout'


@dataclasses.dataclass
class Config:
    format: Options = simple_parsing.subgroups(
        {"csv": CSVOptions, "json": JSONOptions},
        default=CSVOptions(),
    )


def _measurement_fields() -> typing.List[str]:
    return [field.name for field in dataclasses.fields(PMS5003Measurement)]


async def run_json(options: JSONOptions):
    async with aiofiles.open(options.file, mode='w') as file:
        async with open_pms(port=options.port) as pms:
            async for timestamp, current in pms.read(dedupe=options.dedup, warmup=options.warmup):
                await file.write(f"{current.json(timestamp if options.with_timestamp else None)}{os.linesep}")
                await file.flush()


async def run_csv(options: CSVOptions):
    async with aiofiles.open(options.file, mode='w') as file:
        async with open_pms(port=options.port) as pms:
            if options.with_header:
                field_names = ','.join(_measurement_fields())
                await file.write(f"{'timestamp,' if options.with_timestamp else ''}{field_names}{os.linesep}")
                await file.flush()
            async for timestamp, current in pms.read(dedupe=options.dedup, warmup=options.warmup):
                await file.write(f"{current.csv(timestamp if options.with_timestamp else None)}{os.linesep}")
                await file.flush()


async def run(config: Config):
    if isinstance(config.format, CSVOptions):
        await run_csv(config.format)
    elif isinstance(config.format, JSONOptions):
        await run_json(config.format)
    else:
        raise RuntimeError("Bad format")


def main():
    parser = simple_parsing.ArgumentParser()
    parser.add_arguments(Config, dest="format")
    args = parser.parse_args()
    try:
        asyncio.run(run(args.format))
    except KeyboardInterrupt:
        sys.exit()


if __name__ == 'main':
    main()