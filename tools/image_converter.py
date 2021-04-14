import base64

import cv2


def cv2base64(image):
    base64_str = cv2.imencode('.jpg', image)[1].tobytes()
    base64_str = base64.b64encode(base64_str)
    return base64_str.decode('utf8')
