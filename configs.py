import os

BASE_DIR = os.path.dirname(__file__)

PING_NETWORK = 'www.baidu.com'
CAMERA_FILE = 0
PADDLE_INFERENCE_MODEL_DIR = os.path.join(BASE_DIR, 'paddle_inference_infer_model')
PADDLELITE_MODEL = os.path.join(BASE_DIR, 'model.nb')
INFER_THRESHOLD = 0.03
GPIO_POWER_PIN_NUM = 11