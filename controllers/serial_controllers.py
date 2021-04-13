import serial

import configs
from monitor_logger.logger import get_logger


__all__ = ['SerialController',]


class SerialController:
    def __init__(self):
        self.port = configs.SERIAL_PORT
        self.bps = configs.SERIAL_BAUD_RATE
        self.timeout = configs.SERIAL_TIMEOUT
        self.logger = get_logger()
        try:
            self.main_engine = serial.Serial(self.port, self.bps, timeout=self.timeout)
        except Exception as e:
            self.logger.error('BaseSerialContorler.__init__: %s', e.__str__())

    def shutdown(self):
        self._send_data('0'.encode('utf8'))

    def boot(self):
        self._send_data('1'.encode('utf8'))

    def close(self):
        self.main_engine.close()

    def _send_data(self, data):
        self.main_engine.write(data)
