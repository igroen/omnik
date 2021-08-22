import argparse
import json
import time

from influxdb import InfluxDBClient

from .inverter import (
    Inverter,
    InverterException,
)

MIN_REPEAT_INTERVAL = 60


def _repeat_interval(value):
    int_value = int(value)
    if int_value < MIN_REPEAT_INTERVAL:
        raise argparse.ArgumentTypeError(
            f"repeat_interval should be >= {MIN_REPEAT_INTERVAL}",
        )
    return int_value


def _parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i", "--ip",
        type=str,
        required=True,
        help="ip address of the inverter",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        required=True,
        help="port number of the inverter",
    )
    parser.add_argument(
        "-s", "--serial-number",
        type=int,
        required=True,
        help="serial number of the logger",
    )
    parser.add_argument(
        "-r", "--repeat-interval",
        type=_repeat_interval,
        help="repeat every n seconds",
    )
    parser.add_argument(
        "--influxdb-host",
        type=str,
        default="localhost",
        help="hostname or ip of influxdb instance",
    )
    parser.add_argument(
        "--influxdb-port",
        type=int,
        default=8086,
        help="port number of influxdb instance",
    )
    parser.add_argument(
        "--influxdb-database",
        type=str,
        help="name of the influxdb database to store datapoints",
    )

    return parser.parse_args()


def main():
    args = _parse_arguments()
    inverter = Inverter(
        ip=args.ip,
        port=args.port,
        serial_number=args.serial_number,
    )

    if args.influxdb_database is None:
        print(json.dumps(inverter.get_data(), indent=4))
        return

    client = InfluxDBClient(
        host=args.influxdb_host,
        port=args.influxdb_port,
        database=args.influxdb_database,
    )
    client.create_database(args.influxdb_database)

    while True:
        try:
            inverter_data = inverter.get_data()
        except InverterException:
            pass
        else:
            client.write_points([{
                "measurement": "production_metrics",
                "time": inverter_data["time"],
                "fields": {
                    "power": inverter_data["power"],
                    "energy_today": inverter_data["energy_today"],
                    "energy_total": inverter_data["energy_total"],
                    "input_voltage": inverter_data["input_voltage"],
                    "input_current": inverter_data["input_current"],
                    "output_voltage": inverter_data["output_voltage"],
                    "output_current": inverter_data["output_current"],
                    "output_frequency": inverter_data["output_frequency"],
                    "temperature": inverter_data["temperature"],
                },
            }])
        finally:
            if args.repeat_interval is None:
                break
            time.sleep(args.repeat_interval)
