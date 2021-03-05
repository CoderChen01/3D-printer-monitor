import RPi.GPIO as GPIO


class GPIOControler:
    def __init__(self, pin_num, is_output=True):
        self.pin_num = pin_num
        self.is_output = is_output

    def shutdown(self):
        if not self.is_output:
            return
        GPIO.output(self.pin_num, GPIO.HIGH)

    def boot(self):
        if not self.is_output:
            return
        GPIO.output(self.pin_num, GPIO.LOW)

    def __enter__(self):
        GPIO.setmode(GPIO.BOARD)
        if self.is_output:
            GPIO.setup(self.pin_num, GPIO.OUT)
        else:
            GPIO.setup(self.pin_num, GPIO.IN)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        GPIO.cleanup()
