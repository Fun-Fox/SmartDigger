import base64
import json

import requests


def read_image_to_base64(image_path):
    """读取图片文件并转换为Base64字符串"""
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def read_xml_file(xml_path):
    """读取XML文件内容"""
    with open(xml_path, 'r', encoding='utf-8') as xml_file:
        return xml_file.read()


def test_diagnose_api(image_path, xml_path, device_name):
    """测试诊断接口"""
    # 将图片转换为Base64编码
    screenshot_base64 = read_image_to_base64(image_path)

    # 读取XML文件内容
    xml_content = read_xml_file(xml_path)

    # 构建请求数据
    data = {
        "screenshot": screenshot_base64,
        "xml_file": xml_content,
        "devices_name": device_name
    }
    # print(data)
    # 将 data 保存到 JSON 文件
    with open("output.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)
    # 发送POST请求到诊断接口
    response = requests.post("http://localhost:5000/api/v1/diagnose", json=data)
    response.encoding = 'utf-8'

    # 检查响应状态码
    if response.status_code == 200:
        result = response.json()
        print(result)
    else:
        print("诊断失败:", response.text.encode('utf-8').decode('unicode_escape'))


if __name__ == '__main__':
    # 替换为实际的图片路径、XML文件路径和设备名称
    image_path = "test-3.jpeg"
    xml_path = "hierarchy-3.xml"
    device_name = "172.25.13.8:5555"

    test_diagnose_api(image_path, xml_path, device_name)
