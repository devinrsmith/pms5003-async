import asyncio
import dataclasses
import sys
import typing

from .measurement import PMS5003Measurement
from .serial import PMS5003Serial, open_pms


__version__ = '0.0.1.dev3'


def _measurement_fields() -> typing.List[str]:
    return [field.name for field in dataclasses.fields(PMS5003Measurement)]


async def _write_csv(pms: PMS5003Serial, with_header=True, with_timestamp=True, dedupe=True, warmup=30.0, file=sys.stdout):
    if with_header:
        field_names = ','.join(_measurement_fields())
        print(f"{'timestamp,' if with_timestamp else ''}{field_names}", file=file)
    async for timestamp, current in pms.read(dedupe=dedupe, warmup=warmup):
        print(f"{current.csv(timestamp if with_timestamp else None)}", file=file)


async def _write_json(pms: PMS5003Serial, with_timestamp=True, dedupe=True, warmup=30.0, file=sys.stdout):
    async for timestamp, current in pms.read(dedupe=dedupe, warmup=warmup):
        print(f"{current.json(timestamp if with_timestamp else None)}", file=file)


async def write_csv(port='/dev/ttyAMA0', with_header=True, with_timestamp=True, dedupe=True, warmup=30.0, file=sys.stdout):
    async with open_pms(port=port) as pms:
        await _write_csv(pms, with_header, with_timestamp, dedupe, warmup, file)        


async def write_json(port='/dev/ttyAMA0', with_timestamp=True, dedupe=True, warmup=30.0, file=sys.stdout):
    async with open_pms(port=port) as pms:
        await _write_json(pms, with_timestamp, dedupe, warmup, file)


def write_csv_main():
    # TODO: argparse CLI
    print('Writing csv. May be short warmup delay...', file=sys.stderr)
    try:
        asyncio.run(write_csv())
    except KeyboardInterrupt:
        sys.exit()


def write_json_main():
    # TODO: argparse CLI
    print("Writing json. May be short warmup delay...", file=sys.stderr)
    try:
        asyncio.run(write_json())
    except KeyboardInterrupt:
        sys.exit()


# TODO: single entrypoint, single main
