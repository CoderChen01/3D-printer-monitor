import os

# project root directory
BASE_DIR = os.path.dirname(__file__)

# the site used to test whether the network is working properly
PING_NETWORK = 'www.baidu.com'

# camera address
CAMERA_FILE = 0
# infer module path
INFER = 'infers.paddlelite_infer'
# preprocess params
IMAGE_PREPROCESS_PARAM = {
    'Resize': {'image_shape': [608, 608],
               'interp': 2,
               'max_size': 0,
               'target_size': 608,
               'use_cv2': True,
               'arch': 'YOLO'},
    'Normalize': {'is_channel_first': False,
                  'is_scale': True,
                  'mean': [0.485, 0.456, 0.406],
                  'std': [0.229, 0.224, 0.225]},
    'Permute': {'channel_first': True,
                'to_bgr': False}
}
# the resulting filter threshold
INFER_THRESHOLD = 0.03
PREDICT_LABELS = ['failure',]
# model file path
PADDLE_INFERENCE_MODEL_DIR = os.path.join(BASE_DIR, 'paddle_inference_infer_model')
PADDLELITE_MODEL = os.path.join(BASE_DIR, 'model.nb')

# logger configuration, logger file name
LOGGER_NAME = 'monitor'


# controlLers configuration
CONTROLLER = 'controllers.serial_controllers.SerialController'
SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUD_RATE = 9600
SERIAL_TIMEOUT = 3
# CONTROLLER = 'controlers.GPIOControler'
# gpio controlLers configuration
# GPIO_POWER_PIN_NUM = 11
