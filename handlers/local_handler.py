import configs
from monitor_logger.logger import get_logger
from tools import visualize_box_mask
from tools import Incidents, Label, Location, upload_incident, cv2base64

logger = get_logger()


def local_handler(frame, result):
    image = cv2base64(frame)
    incidents = Incidents()
    np_boxes = result['boxes']
    for box in np_boxes:
        clsid, bbox, score = int(box[0]), box[2:], box[1]
        xmin, ymin, xmax, ymax = bbox
        w = xmax - xmin
        h = ymax - ymin
        location = Location(xmin, ymin, w, h)
        label = Label('failue',
                      '置信度',
                      str(score))
        incidents.add_incident(location, label)
    incidents.add_result('all_count',
                         '堆积混乱总目标数',
                         str(result['num']),
                         {'color': 'red', 'font-size': '15px'}) \
             .add_result('device_number',
                         '设备号',
                         '3D10191009',
                         {'color': 'red', 'font-size': '15px'}) \
             .add_result('is_ok',
                         '是否成功关闭',
                         '是',
                         {'color': 'red', 'font-size': '15px'})
    upload_incident(domain=configs.SERVER_ADRESS, incident_image=image, result=incidents.get_data())