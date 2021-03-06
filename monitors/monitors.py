import time
from datetime import datetime
import threading
import multiprocessing as mp

import cv2

import configs
from monitor_logger.logger import get_logger
from controllers import get_controller
from infers.load_infer import get_infer
from handlers import local_handler
from tools import GoodVideoCpature

logger = get_logger()


class Monitor:
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5):
        self.uuid = uuid
        self.all_time = all_time * 60
        self.inspection_interval = inspection_interval * 60
        self.failure_num = failure_num
        self.shared_queue = mp.Queue()
        self._is_run = mp.Value('i', 0)
        self._controller = get_controller()
        self._boot()

    def run(self):
        raise NotImplementedError('You must implement run method')

    def _handler(self):
        raise NotImplementedError('You must implement handler method')

    def _detector(self):
        capture = GoodVideoCpature.create(configs.CAMERA_FILE)
        capture.start_read()
        if not capture.is_started():
            EXIT = -1
            logger.error('Monitor._detector: %s',
                         'Can\'t turn on the camera')
            capture.stop_read()
            capture.release()
            self.set_run_status(False)
            return
        logger.info('Monitor._detector: %s',
                    'Start monitor...')
        start_time = time.time()
        while True:
            if time.time() - start_time >= self.all_time:
                capture.stop_read()
                capture.release()
                self.set_run_status(False)
                return
            if not self.get_run_status():
                capture.stop_read()
                capture.release()
                return
            retval, frame = capture.read_latest_frame()
            if not retval:
                logger.warning('Monitor._detector: %s',
                               'No frame was read')
                continue
            logger.info('Monitor._detector: %s', 'get a frame')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.shared_queue.put({
                'frame': frame,
                'current_time': current_time
            })
            time.sleep(self.inspection_interval)

    def _shutdown(self):
        self._controller.shutdown()

    def _boot(self):
        self._controller.boot()

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
        self._controller.close()
