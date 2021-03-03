import os
import time
import logging
import subprocess
import multiprocessing as mp

import cv2
import RPi.GPIO as GPIO

import configs
from failure_predictor import infer


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('monitor.log', mode='w')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formater = logging.Formatter('%(asctime)s %(name)s'
                             ' %(levelname)s %(message)s')
fh.setFormatter(formater)
ch.setFormatter(formater)

logger.addHandler(fh)
logger.addHandler(ch)


class Monitor:
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 alarm_num=3,
                 alarm_interval=2,
                 event_num=5):
        self.uuid = uuid
        self.all_time = all_time * 60
        self.inspection_interval = inspection_interval * 60
        self.failure_num = failure_num
        self.alarm_num = alarm_num
        self.alarm_interval = alarm_interval * 60
        self.event_num = event_num
        self.shared_queue = mp.Queue()
        self._is_run = mp.Value('i', 0)

    def detector(self):
        self.set_run_status(True)
        predictor = infer.Detector(configs.MODEL_DIR)
        start_time = time.time()
        capture = cv2.VideoCapture(configs.CAMERA_FILE)
        if not capture.isOpened():
            EXIT = -1
            logger.error('Monitor.detector: %s',
                         'Can\'t turn on the camera')
            capture.release()
            self.set_run_status(False)
            return

        while True:
            if time.time() - start_time >= self.all_time:
                capture.release()
                self.set_run_status(False)
                return
            if not self.get_run_status():
                capture.release()
                return
            retval, frame = capture.read()
            if not retval:
                logger.warning('Monitor.detector: %s',
                               'No frame was read')
                continue
            time.sleep(self.inspection_interval)
            result = predictor.predict(frame,
                                   threshold=configs.INFER_THRESHOLD)
            if result.get('num', 0) <= self.failure_num:
                self.shared_queue.put(False)
                continue
            self.shared_queue.put(True)

    def local_handler(self):
        self.set_run_status(True)
        event_num = 0
        start_time = time.time()
        while True:
            if time.time() - start_time >= self.all_time:
                self.set_run_status(False)
                return
            if not self.get_run_status():
                return
            if self.shared_queue.get():
                event_num += 1
            if event_num == self.event_num:
                logger.info('Monitor.local_handler: %s',
                            'When the number of detection'
                            ' events exceeds the predetermined threshold,'
                            ' the switch is automatically turned off')
                self.set_run_status(False)
                event_num = 0
                self.shutdown()

    def online_handler(self):
        pass

    def local_monitor(self):
        return self.run_monitor(self.detector, self.local_handler)

    def online_monitor(self):
        od, oh = self.run_monitor(self.detector, self.online_handler)
        while True:
            while self.check_network():
                if not od.is_alive() and not oh.is_alive():
                    logger.info('Monitor.online_monitor: %s',
                                'Finished')
                    return
                continue
            logger.warning('Monitor.online_monitor: %s',
                           'Network exception, switch running mode')
            ld, lh = self.change_monitor(od, oh, self.local_monitor)
            while not self.check_network():
                if not ld.is_alive() and not lh.is_alive():
                    return
                continue
            logger.warning('Monitor.online_monitor: %s',
                           'Network exception, switch running mode')
            od, oh = self.change_monitor(ld, lh, self.online_monitor)

    def change_monitor(self, old_detector, old_handler, new_monitor):
        self.set_run_status(False)
        while old_detector.is_alive() and old_handler.is_alive():
            continue
        return new_monitor()

    @staticmethod
    def check_network():
        fnull = open(os.devnull, 'w')
        retval = subprocess.call('ping ' + configs.PING_NETWORK + ' -n 2',
                                 shell=True,
                                 stdout=fnull,
                                 stderr=fnull)
        fnull.close()
        return False if retval else True

    @staticmethod
    def run_monitor(detector, handler):
        d = mp.Process(target=detector)
        h = mp.Process(target=handler)
        d.start()
        h.start()
        return d, h

    def set_run_status(self, is_run):
        if is_run:
            self._is_run.value = 1
        else:
            self._is_run.value = 0

    def get_run_status(self):
        return self._is_run.value

    @staticmethod
    def shutdown():
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(11, GPIO.OUT)
        GPIO.output(11, GPIO.HIGH)
        GPIO.cleanup()

    def online_close(self):
        pass

if __name__ == '__main__':
    from uuid import uuid4
    monitor = Monitor(uuid4(), 200)
    monitor.local_monitor()