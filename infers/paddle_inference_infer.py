import os
import yaml
from functools import reduce

import numpy as np
import paddle.fluid as fluid

from tools.preprocess import *
import configs


def decode_image(im_file, im_info):
    """read rgb image
    Args:
        im_file (str/np.ndarray): path of image/ np.ndarray read by cv2
        im_info (dict): info of image
    Returns:
        im (np.ndarray):  processed image (np.ndarray)
        im_info (dict): info of processed image
    """
    if isinstance(im_file, str):
        with open(im_file, 'rb') as f:
            im_read = f.read()
        data = np.frombuffer(im_read, dtype='uint8')
        im = cv2.imdecode(data, 1)  # BGR mode, but need RGB mode
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im_info['origin_shape'] = im.shape[:2]
        im_info['resize_shape'] = im.shape[:2]
    else:
        im = im_file
        im_info['origin_shape'] = im.shape[:2]
        im_info['resize_shape'] = im.shape[:2]
    return im, im_info


def create_inputs(im, im_info, model_arch='YOLO'):
    """generate input for different model type
    Args:
        im (np.ndarray): image (np.ndarray)
        im_info (dict): info of image
        model_arch (str): model type
    Returns:
        inputs (dict): input of model
    """
    inputs = {}
    inputs['image'] = im
    origin_shape = list(im_info['origin_shape'])
    resize_shape = list(im_info['resize_shape'])
    scale_x, scale_y = im_info['scale']
    if 'YOLO' in model_arch:
        im_size = np.array([origin_shape]).astype('int32')
        inputs['im_size'] = im_size
    elif 'RetinaNet' in model_arch:
        scale = scale_x
        im_info = np.array([resize_shape + [scale]]).astype('float32')
        inputs['im_info'] = im_info
    elif ('RCNN' in model_arch) or ('FCOS' in model_arch):
        scale = scale_x
        im_info = np.array([resize_shape + [scale]]).astype('float32')
        im_shape = np.array([origin_shape + [1.]]).astype('float32')
        inputs['im_info'] = im_info
        inputs['im_shape'] = im_shape
    elif 'TTF' in model_arch:
        scale_factor = np.array([scale_x, scale_y] * 2).astype('float32')
        inputs['scale_factor'] = scale_factor
    return inputs


class Config:
    """set config of preprocess, postprocess and visualize
    Args:
        model_dir (str): root path of model.yml
    """
    support_models = [
        'YOLO',
        'SSD',
        'RetinaNet',
        'RCNN',
        'Face',
        'TTF',
        'FCOS',
    ]

    def __init__(self, model_dir):
        # parsing Yaml config for Preprocess
        deploy_file = os.path.join(model_dir, 'infer_cfg.yml')
        with open(deploy_file) as f:
            yml_conf = yaml.safe_load(f)
        self.check_model(yml_conf)
        self.arch = yml_conf['arch']
        self.preprocess_infos = yml_conf['Preprocess']
        self.use_python_inference = yml_conf['use_python_inference']
        self.min_subgraph_size = yml_conf['min_subgraph_size']
        self.labels = yml_conf['label_list']
        self.mask_resolution = None
        if 'mask_resolution' in yml_conf:
            self.mask_resolution = yml_conf['mask_resolution']

    def check_model(self, yml_conf):
        """
        Raises:
            ValueError: loaded model not in supported model type
        """
        for support_model in self.support_models:
            if support_model in yml_conf['arch']:
                return True
        raise ValueError("Unsupported arch: {}, expect {}".format(yml_conf[
            'arch'], self.support_models))


def load_predictor(run_mode='fluid',
                   batch_size=1,
                   use_gpu=False,
                   min_subgraph_size=3):
    """set AnalysisConfig, generate AnalysisPredictor
    Args:
        model_dir (str): root path of __model__ and __params__
        use_gpu (bool): whether use gpu
    Returns:
        predictor (PaddlePredictor): AnalysisPredictor
    Raises:
        ValueError: predict by TensorRT need use_gpu == True.
    """
    if not use_gpu and not run_mode == 'fluid':
        raise ValueError(
            "Predict by TensorRT mode: {}, expect use_gpu==True, but use_gpu == {}"
            .format(run_mode, use_gpu))
    if run_mode == 'trt_int8':
        raise ValueError("TensorRT int8 mode is not supported now, "
                         "please use trt_fp32 or trt_fp16 instead.")
    precision_map = {
        'trt_int8': fluid.core.AnalysisConfig.Precision.Int8,
        'trt_fp32': fluid.core.AnalysisConfig.Precision.Float32,
        'trt_fp16': fluid.core.AnalysisConfig.Precision.Half
    }
    config = fluid.core.AnalysisConfig(
        os.path.join(configs.PADDLE_INFERENCE_MODEL_DIR, '__model__'),
        os.path.join(configs.PADDLE_INFERENCE_MODEL_DIR, '__params__'))
    if use_gpu:
        # initial GPU memory(M), device ID
        config.enable_use_gpu(100, 0)
        # optimize graph and fuse op
        config.switch_ir_optim(True)
    else:
        config.disable_gpu()

    if run_mode in precision_map.keys():
        config.enable_tensorrt_engine(
            workspace_size=1 << 10,
            max_batch_size=batch_size,
            min_subgraph_size=min_subgraph_size,
            precision_mode=precision_map[run_mode],
            use_static=False,
            use_calib_mode=False)

    # disable print log when predict
    config.disable_glog_info()
    # enable shared memory
    config.enable_memory_optim()
    # disable feed, fetch OP, needed by zero_copy_run
    config.switch_use_feed_fetch_ops(False)
    predictor = fluid.core.create_paddle_predictor(config)
    return predictor


def load_executor(model_dir, use_gpu=False):
    if use_gpu:
        place = fluid.CUDAPlace(0)
    else:
        place = fluid.CPUPlace()
    exe = fluid.Executor(place)
    program, feed_names, fetch_targets = fluid.io.load_inference_model(
        dirname=model_dir,
        executor=exe,
        model_filename='__model__',
        params_filename='__params__')
    return exe, program, fetch_targets


class Detector:
    """
    Args:
        model_dir (str): root path of __model__, __params__ and infer_cfg.yml
        use_gpu (bool): whether use gpu
    """

    def __init__(self,
                 model_dir,
                 use_gpu=False,
                 run_mode='fluid',
                 threshold=0.5):
        self.config = Config(model_dir)
        if self.config.use_python_inference:
            self.executor, self.program, self.fecth_targets = load_executor(
                model_dir, use_gpu=use_gpu)
        else:
            self.predictor = load_predictor(
                model_dir,
                run_mode=run_mode,
                min_subgraph_size=self.config.min_subgraph_size,
                use_gpu=use_gpu)
        self.preprocess_ops = []
        for op_info in self.config.preprocess_infos:
            op_type = op_info.pop('type')
            if op_type == 'Resize':
                op_info['arch'] = self.config.arch
            self.preprocess_ops.append(eval(op_type)(**op_info))

    def preprocess(self, im):
        # process image by preprocess_ops
        im_info = {
            'scale': [1., 1.],
            'origin_shape': None,
            'resize_shape': None,
        }
        im, im_info = decode_image(im, im_info)
        for operator in self.preprocess_ops:
            im, im_info = operator(im, im_info)
        im = np.array((im, )).astype('float32')
        inputs = create_inputs(im, im_info, self.config.arch)
        return inputs, im_info

    def postprocess(self, np_boxes, np_masks, im_info, threshold=0.5):
        # postprocess output of predictor
        results = {}
        if self.config.arch in ['SSD', 'Face']:
            w, h = im_info['origin_shape']
            np_boxes[:, 2] *= h
            np_boxes[:, 3] *= w
            np_boxes[:, 4] *= h
            np_boxes[:, 5] *= w
        expect_boxes = (np_boxes[:, 1] > threshold) & (np_boxes[:, 0] > -1)
        np_boxes = np_boxes[expect_boxes, :]
        def handle_round(box):
            new_box = [int(box[0]), round(box[1], 4),
                       round(box[2], 2), round(box[3], 2),
                       round(box[4], 2), round(box[5], 2)]
            return new_box
        np_boxes = list(map(handle_round, np_boxes))
        results['boxes'] = np_boxes
        results['num'] = len(np_boxes)
        if np_masks is not None:
            np_masks = np_masks[expect_boxes, :, :, :]
            results['masks'] = np_masks
        return results

    def predict(self,
                image,
                threshold=configs.INFER_THRESHOLD,
                warmup=0,
                repeats=1,
                run_benchmark=False):
        """
        Args:
            image (str/np.ndarray): path of image/ np.ndarray read by cv2
            threshold (float): threshold of predicted box' score
        Returns:
            results (dict): include 'boxes': np.ndarray: shape:[N,6], N: number of box,
                            matix element:[class, score, x_min, y_min, x_max, y_max]
                            MaskRCNN's results include 'masks': np.ndarray:
                            shape:[N, class_num, mask_resolution, mask_resolution]
        """
        inputs, im_info = self.preprocess(image)
        np_boxes, np_masks = None, None
        if self.config.use_python_inference:
            for i in range(warmup):
                outs = self.executor.run(self.program,
                                         feed=inputs,
                                         fetch_list=self.fecth_targets,
                                         return_numpy=False)
            for i in range(repeats):
                outs = self.executor.run(self.program,
                                         feed=inputs,
                                         fetch_list=self.fecth_targets,
                                         return_numpy=False)

            np_boxes = np.array(outs[0])
            if self.config.mask_resolution is not None:
                np_masks = np.array(outs[1])
        else:
            input_names = self.predictor.get_input_names()
            for i in range(len(input_names)):
                input_tensor = self.predictor.get_input_tensor(input_names[i])
                input_tensor.copy_from_cpu(inputs[input_names[i]])

            for i in range(warmup):
                self.predictor.zero_copy_run()
                output_names = self.predictor.get_output_names()
                boxes_tensor = self.predictor.get_output_tensor(output_names[0])
                np_boxes = boxes_tensor.copy_to_cpu()
                if self.config.mask_resolution is not None:
                    masks_tensor = self.predictor.get_output_tensor(
                        output_names[1])
                    np_masks = masks_tensor.copy_to_cpu()

            for i in range(repeats):
                self.predictor.zero_copy_run()
                output_names = self.predictor.get_output_names()
                boxes_tensor = self.predictor.get_output_tensor(output_names[0])
                np_boxes = boxes_tensor.copy_to_cpu()
                if self.config.mask_resolution is not None:
                    masks_tensor = self.predictor.get_output_tensor(
                        output_names[1])
                    np_masks = masks_tensor.copy_to_cpu()

        # do not perform postprocess in benchmark mode
        results = []
        if not run_benchmark:
            if reduce(lambda x, y: x * y, np_boxes.shape) < 6:
                results = {'boxes': np.array([]), 'num': 0}
            else:
                results = self.postprocess(
                    np_boxes, np_masks, im_info, threshold=threshold)

        return results
