import requests
from uuid import uuid4
import json


class Text:
    def __init__(self,
                 key,
                 key_desc,
                 value,
                 style=None):
        if style is None:
            style = {'color': 'red'}
        self.key = key
        self.key_desc = key_desc
        self.value = value
        self.style = style

    def get_data(self):
        return self.__dict__


class Result(Text):
    pass


class Label(Text):
    pass


class Location:
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def get_data(self):
        return self.__dict__


class Incident:
    def __init__(self, location, label, style=None):
        if style is None:
            style = {
                "color": "red",
                "stroke": {
                    "width": 2
                }
            }
        self.location = location
        self.label = label
        self.style = style

    def get_data(self):
        return self.__dict__


class Incidents:
    def __init__(self):
        self.incidents = []
        self.results = []

    def add_incident(self, location, label, style=None):
        incident = Incident(location.get_data(), label.get_data(), style)
        self.incidents.append(incident.get_data())
        return self

    def add_result(self, key, key_desc, value, style=None):
        result = Result(key, key_desc, value, style)
        self.results.append(result.get_data())
        return self

    def get_data(self):
        return self.__dict__


def upload_incident(domain, incident_image, result):
    """
    传入域名和端口号，base64图片，分析结果上传服务器
    :param domain: domain + 端口
    :param incident_image: base64图片编码
    :param result: json 参照README文件
    :return: bool
    """
    url = 'http://' + domain + '/incidents/create-incident'
    try:
        response = requests.post(
            url=url,
            json={
                'incident_id': str(uuid4()),
                'incident_image': incident_image,
                'response': json.dumps(result),
                'occurence_time': datetime.datetime.now().__str__()
            },
            headers={
                'Content-Type': 'application/json'
            },
            timeout=100
        )
    except (
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout,
        requests.exceptions.RetryError):
        return False

    if response.status_code == 200:
        response = response.json()
        if response['code']:
            return True

    return False
