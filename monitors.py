import os
import time
import logging
import subprocess
import importlib
import multiprocessing as mp

import cv2

import configs
from gpio_controlers import GPIOControler

logger = logging.getLogger(configs.LOGGER_NAME)


def check_network():
    fnull = open(os.devnull, 'w')
    retval = subprocess.call('ping ' + configs.PING_NETWORK + ' -n 2',
                             shell=True,
                             stdout=fnull,
                             stderr=fnull)
    fnull.close()
    return False if retval else True


class Monitor:
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 infer='paddlelite_infer'):
        self._boot()
        self.infer = infer
        self.uuid = uuid
        self.all_time = all_time * 60
        self.inspection_interval = inspection_interval * 60
        self.failure_num = failure_num
        self.shared_queue = mp.Queue()
        self._is_run = mp.Value('i', 0)

    def run(self):
        raise NotImplementedError('You must implement run method')

    def _handler(self):
        raise NotImplementedError('You must implement handler method')

    def _detector(self):
        if self.infer == 'paddle_inference_infer':
            infer_module = importlib.import_module(self.infer)
            predictor = infer_module.Detector(configs.PADDLE_INFERENCE_MODEL_DIR)
        elif self.infer == 'paddlelite_infer':
            infer_module = importlib.import_module(self.infer)
            predictor = infer_module.Detector(configs.PADDLELITE_MODEL,
                                              configs.IMAGE_PREPROCESS_PARAM)
        else:
            logger.error('Monitor._detector: %s',
                         'The Infer parameter can only be paddle_inference_infer'
                         ' or paddlelite_infer!')
            self.set_run_status(False)
            return
        start_time = time.time()
        capture = cv2.VideoCapture(configs.CAMERA_FILE)
        if not capture.isOpened():
            EXIT = -1
            logger.error('Monitor._detector: %s',
                         'Can\'t turn on the camera')
            capture.release()
            self.set_run_status(False)
            return
        logger.info('Monitor._detector: %s',
                    'Start monitor...')
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
            logger.debug('Monitor._detector: %s',
                         'predicting...')
            result = predictor.predict(frame,
                                       threshold=configs.INFER_THRESHOLD)
            logger.debug('Monitor._detector: %s',
                         'finished...')
            if result.get('num', 0) <= self.failure_num:
                self.shared_queue.put(False)
                logger.debug('Monitor._detector: %s',
                             'put False')
                continue
            self.shared_queue.put(True)
            time.sleep(self.inspection_interval)
            logger.debug('Monitor._detector: %s',
                         'put True')

    @staticmethod
    def _shutdown():
        GPIOControler(configs.GPIO_POWER_PIN_NUM).shutdown()

    @staticmethod
    def _boot():
        GPIOControler(configs.GPIO_POWER_PIN_NUM).boot()

    def _run_monitor(self):
        self.set_run_status(True)
        d = mp.Process(target=self._detector)
        h = mp.Process(target=self._handler)
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

    def __del__(self):
        GPIOControler.close()


class LocalMonitor(Monitor):
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 infer='paddlelite_infer',
                 event_num=5):
        super(LocalMonitor, self).__init__(uuid,
                                           all_time,
                                           inspection_interval,
                                           failure_num,
                                           infer)
        self.event_num = event_num

    def run(self):
        return self._run_monitor()

    def _handler(self):
        event_num = 0
        start_time = time.time()
        while True:
            if time.time() - start_time >= self.all_time:
                self.set_run_status(False)
                return
            if not self.get_run_status():
                return
            if event_num == self.event_num:
                logger.info('LocalMonitor._handler: %s',
                            'When the number of detection'
                            ' events exceeds the predetermined threshold,'
                            ' the switch is automatically turned off')
                self.set_run_status(False)
                event_num = 0
                self._shutdown()
                return
            if self.shared_queue.get():
                event_num += 1
                logger.info('LocalMonitor._handler: %s',
                            'Detect a envent, num: %d' % event_num)


class OnlineMonitor(Monitor):
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 infer='paddlelite',
                 alarm_num=3,
                 alarm_interval=2):
        super(OnlineMonitor, self).__init__(uuid, all_time)
        self.alarm_num = alarm_num
        self.alarm_interval = alarm_interval * 60

    def run(self):
        pass

    def _handler(self):
        pass
