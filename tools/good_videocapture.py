import cv2


class GoodVideoCpature(cv2.VideoCapture):
    def __init__(self, url, *args, **kwargs):
        super(GoodVideoCpature, self).__init__(url, *args, **kwargs)
        self.frame_receiver = None
        self._result = (None, None)
        self._reading = False

    @staticmethod
    def create(url):
        rtscap = GoodVideoCpature(url)
        rtscap.frame_receiver = threading.Thread(target=rtscap.recv_frame)
        rtscap.frame_receiver.daemon = True
        return rtscap

    def is_started(self):
        ok = self.isOpened()
        if ok and self._reading:
            ok = self.frame_receiver.is_alive()
        return ok

    def get_status(self):
        return self._reading

    def recv_frame(self):
        while self.isOpened():
            if not self._reading:
                return
            self._result = self.read()
        self._reading = False

    def read_latest_frame(self):
        return self._result

    def start_read(self):
        self._reading = True
        self.frame_receiver.start()

    def stop_read(self):
        self._reading = False
        if self.frame_receiver.is_alive():
            self.frame_receiver.join()