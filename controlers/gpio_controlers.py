import RPi.GPIO as GPIO


class GPIOControler:
    def __init__(self, pin_num, is_output=True):
        self.pin_num = pin_num
        self.is_output = is_output
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        if self.is_output:
            GPIO.setup(self.pin_num, GPIO.OUT)
        else:
            GPIO.setup(self.pin_num, GPIO.IN)

    def shutdown(self):
        if not self.is_output:
            return
        GPIO.output(self.pin_num, GPIO.HIGH)

    def boot(self):
        if not self.is_output:
            return
        GPIO.output(self.pin_num, GPIO.LOW)

    @staticmethod
    def close():
        GPIO.cleanup()
