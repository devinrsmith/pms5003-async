import dataclasses
import datetime
import json


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
        return json.dumps({**timestamp_dict, **measurement_dict}, separators=(',', ':'))
