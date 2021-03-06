import RPi.GPIO as GPIO

import configs


__all__ = ['GPIOController',]


class GPIOController:
    def __init__(self):
        self.pin_num = configs.GPIO_POWER_PIN_NUM
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin_num, GPIO.OUT)

    def shutdown(self):
        GPIO.output(self.pin_num, GPIO.HIGH)

    def boot(self):
        GPIO.output(self.pin_num, GPIO.LOW)

    def close(self):
        pass
