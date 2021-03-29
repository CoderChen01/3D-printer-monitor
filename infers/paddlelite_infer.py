from functools import reduce

import cv2
import numpy as np
from paddlelite.lite import *

import configs
from tools.preprocess import Resize, Permute, Normalize


class Detector:
    def __init__(self):
        config = MobileConfig()
        config.set_model_from_file(configs.PADDLELITE_MODEL)  # load yolov3 model
        self._predictor = create_paddle_predictor(config)
        self.preprocess_param = configs.IMAGE_PREPROCESS_PARAM

    def _decode_image(self, image):
        """
        Load the image and pre-process it
        :param image: ndarray
        :return: ndarray, dict
        """
        im_info = {
            'scale': [1., 1.],
            'origin_shape': None,
            'resize_shape': None,
        }
        im = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        im_info['origin_shape'] = im.shape[:2]
        im_info['resize_shape'] = im.shape[:2]
        preprocess_ops = [eval(op_type)(**op_info)
                          for op_type, op_info in self.preprocess_param.items()]
        for operator in preprocess_ops:
            im, im_info = operator(im, im_info)
        im = np.array((im,)).astype('float32')
        return im, im_info

    @staticmethod
    def _create_inputs(im, im_info):
        """
        create yolov3 inputs
        :param im: ndarray
        :param im_info: dict
        :return: yolov3 input
        """
        inputs = {}
        inputs['image'] = im
        origin_shape = list(im_info['origin_shape'])
        resize_shape = list(im_info['resize_shape'])
        scale_x, scale_y = im_info['scale']
        im_size = np.array([origin_shape]).astype('int32')
        inputs['im_size'] = im_size
        return inputs

    @staticmethod
    def _postprocess(np_boxes, im_info, threshold=0.5):
        """
        process yolov3 output
        :param np_boxes: yolov3 output
        :param im_info: dict
        :param threshold: threshold
        :return: dict
        """
        print(threshold)
        results = {}
        expect_boxes = (np_boxes[:, 1] > threshold) & (np_boxes[:, 0] > -1)
        np_boxes = np_boxes[expect_boxes, :]
        def handle_round(box):
            new_box = [int(box[0]), round(box[1], 4),
                       round(box[2], 2), round(box[3], 2),
                       round(box[4], 2), round(box[5], 2)]
            return new_box
        np_boxes = list(map(handle_round, np_boxes))
        print(np_boxes)
        results['boxes'] = np_boxes
        results['num'] = len(np_boxes)
        return results

    def predict(self,
                image,
                threshold=configs.INFER_THRESHOLD):
        """
        predict image
        :param image: ndarray
        :param threshold: threshold
        :return: result
        """
        im, im_info = self._decode_image(image)
        inputs = self._create_inputs(im, im_info)
        input_tensor_image = self._predictor.get_input(0)
        input_tensor_image.resize([1, 3,
                                   im_info['resize_shape'][0],
                                   im_info['resize_shape'][1]])
        image_data = inputs['image'].flatten().tolist()
        input_tensor_image.set_float_data(image_data)

        input_tensor_size = self._predictor.get_input(1)
        input_tensor_size.resize([1, 2])
        size_data = inputs['im_size'].flatten().tolist()
        input_tensor_size.set_int32_data(size_data)

        self._predictor.run()

        np_boxes = self._predictor.get_output(0).float_data()

        try:
            np_boxes = np.array(np_boxes).reshape(-1, 6)
        except Exception:
            return {'boxes': np.array([]), 'num': 0}
        if reduce(lambda x, y: x * y, np_boxes.shape) < 6:
            results = {'boxes': np.array([]), 'num': 0}
        else:
            results = self._postprocess(np_boxes, im_info, threshold)
        return results
