import os

BASE_DIR = os.path.dirname(__file__)

PING_NETWORK = 'www.baidu.com'
CAMERA_FILE = 0
PADDLE_INFERENCE_MODEL_DIR = os.path.join(BASE_DIR, 'paddle_inference_infer_model')
PADDLELITE_MODEL = os.path.join(BASE_DIR, 'model.nb')
INFER_THRESHOLD = 0.03
GPIO_POWER_PIN_NUM = 11
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
PREDICT_LABELS = ['failure',]
LOGGER_NAME = 'monitor'