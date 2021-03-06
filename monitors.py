import os
import time
import logging
import subprocess
import importlib
import multiprocessing as mp

import cv2

import configs
from gpio_controlers import GPIOControler

logger = logging.getLogger(__name__)


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
        self.set_run_status(True)
        infer_module = importlib.import_module(self.infer)
        if self.infer == 'paddle_inference_infer':
            predictor = infer_module.Detector(configs.PADDLE_INFERENCE_MODEL_DIR)
        elif self.infer == 'paddlelite_infer':
            predictor = infer_module.Detector(configs.PADDLELITE_MODEL,
                                              configs.IMAGE_PREPROCESS_PARAM)
        else:
            logger.error('Monitor.detector: %s',
                         'The Infer parameter can only be paddle_inference_infer'
                         ' or paddlelite_infer!')
            self.set_run_status(False)
            return
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
            logger.debug('Monitor._detector: %s',
                         'put True')

    @staticmethod
    def _shutdown():
        GPIOControler(configs.GPIO_POWER_PIN_NUM).shutdown()

    @staticmethod
    def _boot():
        GPIOControler(configs.GPIO_POWER_PIN_NUM).boot()

    def _run_monitor(self):
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
                 infer='paddlelite',
                 event_num=5):
        super(LocalMonitor, self).__init__(uuid, all_time)
        self.event_num = event_num * 60

    def run(self):
        return self._run_monitor()

    def _handler(self):
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
                logger.info('LocalMonitor._handler: %s',
                            'Detect a envent, num: %d' % event_num)
                event_num += 1
            if event_num == self.event_num:
                logger.info('LocalMonitor._handler: %s',
                            'When the number of detection'
                            ' events exceeds the predetermined threshold,'
                            ' the switch is automatically turned off')
                self.set_run_status(False)
                event_num = 0
                self._shutdown()


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


class _Monitor:
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 alarm_num=3,
                 alarm_interval=2,
                 event_num=5,
                 infer='paddlelite_infer'):
        self._boot()
        self.infer = infer
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
        infer_module = importlib.import_module(self.infer)
        if self.infer == 'paddle_inference_infer':
            predictor = infer_module.Detector(configs.PADDLE_INFERENCE_MODEL_DIR)
        elif self.infer == 'paddlelite_infer':
            predictor = infer_module.Detector(configs.PADDLELITE_MODEL,
                                              configs.IMAGE_PREPROCESS_PARAM)
        else:
            logger.error('Monitor.detector: %s',
                         'The Infer parameter can only be paddle_inference_infer'
                         ' or paddlelite_infer!')
            self.set_run_status(False)
            return
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
            from tools.visualize import visualize
            visualize(frame, result, configs.PREDICT_LABELS)
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
                self._shutdown()

    def online_handler(self):
        pass

    def local_monitor(self):
        return self._run_monitor(self.detector, self.local_handler)

    def online_monitor(self):
        od, oh = self._run_monitor(self.detector, self.online_handler)
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
    def _run_monitor(detector, handler):
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
    def _shutdown():
        GPIOControler(configs.GPIO_POWER_PIN_NUM).shutdown()

    @staticmethod
    def _boot():
        GPIOControler(configs.GPIO_POWER_PIN_NUM).boot()

    def online_close(self):
        pass
