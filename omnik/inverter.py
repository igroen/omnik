import functools
import socket
import struct
from datetime import (
    datetime,
    timezone,
)


class InverterException(Exception):
    pass


class Inverter:
    _timeout = 10

    def __init__(self, ip, port, serial_number):
        self.ip = ip
        self.port = port
        self.serial_number = serial_number

    @functools.cached_property
    def _request_data(self):
        double_hex = format(self.serial_number, "x") * 2
        hex_list = [
            bytes.fromhex(double_hex[i:i + 2])
            for i in reversed(range(0, len(double_hex), 2))
        ]
        cs_count = 115 + sum([ord(c) for c in hex_list])
        checksum = bytes.fromhex(format(cs_count, "x")[-2:])

        return (
            b'\x68\x02\x40\x30' +  # noqa:W504
            b''.join(hex_list) +  # noqa:W504
            b'\x01\x00' +  # noqa:W504
            checksum +  # noqa:W504
            b'\x16'
        )

    def _serial_number(self, response_data):
        return response_data[15:31].decode()

    def _power(self, response_data):
        return struct.unpack("!H", response_data[59:61])[0]

    def _energy_today(self, response_data):
        return struct.unpack("!H", response_data[69:71])[0] / 100.0

    def _energy_total(self, response_data):
        return struct.unpack("!I", response_data[71:75])[0] / 10.0

    def _input_voltage(self, response_data):
        return struct.unpack("!H", response_data[33:35])[0] / 10.0

    def _input_current(self, response_data):
        return struct.unpack("!H", response_data[39:41])[0] / 10.0

    def _output_voltage(self, response_data):
        return struct.unpack("!H", response_data[51:53])[0] / 10.0

    def _output_current(self, response_data):
        return struct.unpack("!H", response_data[45:47])[0] / 10.0

    def _output_frequency(self, response_data):
        return struct.unpack("!H", response_data[57:59])[0] / 100.0

    def _temperature(self, response_data):
        temperature = struct.unpack("!H", response_data[31:33])[0] / 10.0

        return temperature if temperature < 250 else 0.0

    def _parse_data(self, response_data):
        try:
            return {
                "serial_number": self._serial_number(response_data),
                "power": self._power(response_data),
                "energy_today": self._energy_today(response_data),
                "energy_total": self._energy_total(response_data),
                "input_voltage": self._input_voltage(response_data),
                "input_current": self._input_current(response_data),
                "output_voltage": self._output_voltage(response_data),
                "output_current": self._output_current(response_data),
                "output_frequency": self._output_frequency(response_data),
                "temperature": self._temperature(response_data),
                "time": datetime.now(timezone.utc).astimezone().isoformat(),
            }
        except Exception as e:
            raise InverterException(
                "An error occurred while parsing response data",
            ) from e

    def get_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self._timeout)
            try:
                s.connect((self.ip, self.port))
                s.send(self._request_data)
                response_data = s.recv(1024)
            except socket.timeout as e:
                raise InverterException(
                    "An error occurred while retrieving data from inverter",
                ) from e
            else:
                return self._parse_data(response_data)
