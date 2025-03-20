from datetime import datetime

from flask import Flask, request, jsonify
from services import vision_analysis
import logging
from dotenv import load_dotenv
import os
import base64

load_dotenv()

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all = ['diagnose']


@app.route('/api/v1/diagnose', methods=['POST'])
def diagnose():
    """
    诊断接口
    请求参数 (JSON):
    - screenshot: Base64 编码的手机屏幕截图
    - xml_file: XML层级结构文本
    返回结果:
    - 诊断分析结果JSON
    """
    try:
        # 获取 JSON 数据
        data = request.get_json()
        if not data or 'screenshot' not in data or 'xml_file' not in data:
            logger.error("请求参数缺失")
            return jsonify({"msg": "请求参数缺失"}), 400

        # 校验 screenshot 和 xml_file 是否为空
        if not data['screenshot'] or not data['xml_file']:
            logger.error("screenshot 或 xml_file 为空")
            return jsonify({"msg": "screenshot 或 xml_file 为空"}), 400

        # 解码 Base64 图像
        screenshot_base64 = data['screenshot']
        try:
            screenshot_bytes = base64.b64decode(screenshot_base64)
        except Exception as e:
            logger.error(f"Base64 解码失败: {str(e)}")
            return jsonify({"msg": "Base64 解码失败"}), 400

        # 动态生成截图文件名
        device_name = data['devices_name']  # 获取设备名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 生成时间戳
        screenshot_filename = f"{device_name}_{timestamp}.png"  # 拼接文件名
        screenshot_path = os.path.join('/tmp', screenshot_filename)  # 生成完整路径

        try:
            with open(screenshot_path, 'wb') as f:
                f.write(screenshot_bytes)
        except Exception as e:
            logger.error(f"保存截图失败: {str(e)}")
            return jsonify({"msg": "保存截图失败"}), 500

        # 动态生成 XML 文件名
        xml_filename = f"{device_name}_{timestamp}_hierarchy.xml"  # 拼接文件名
        xml_path = os.path.join('/tmp', xml_filename)  # 生成完整路径

        # 保存 XML 文本到临时文件
        xml_text = data['xml_file']
        try:
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_text)
        except Exception as e:
            logger.error(f"保存 XML 文件失败: {str(e)}")
            return jsonify({"msg": "保存 XML 文件失败"}), 500

        # 调用诊断服务
        try:
            center_x, center_y = vision_analysis(screenshot_path, xml_path, device_name)
            if center_x is None or center_y is None:
                logger.info("视觉诊断为非弹窗，麻烦人工查看")
                return jsonify({"msg": "视觉诊断为非弹窗，麻烦人工查看"}), 500
            return jsonify({"msg": "视觉诊断为弹窗，点击坐标为：" + str(center_x) + "," + str(center_y),
                            "script": adb_tap_code(device_name, center_x, center_y)}), 200
        except Exception as e:
            logger.error(f"诊断服务调用失败: {str(e)}")
            return jsonify({"msg": "诊断服务调用失败"}), 500

    except Exception as e:
        logger.error(f"诊断失败: {str(e)}")
        return jsonify({"msg": str(e)}), 500


def adb_tap_code(device_name, x, y):
    return f"""
     def tap_on_device(device_name, x, y):
            \"\"\"
            在指定设备的屏幕上模拟点击指定坐标
            :param device_name: 设备名称（可通过 get_device_name 获取）
            :param x: 点击的 X 坐标
            :param y: 点击的 Y 坐标
            \"\"\"
            try:
                # 使用 adb shell input tap 命令模拟点击
                subprocess.run(
                    ['adb', '-s', device_name, 'shell', 'input', 'tap', str(x), str(y)],
                    check=True
                )
                logger.info(f"在设备 {device_name} 上成功点击坐标 ({x}, {y})")
            except subprocess.CalledProcessError as e:
                logger.error(f"在设备 {device_name} 上点击坐标 ({x}, {y}) 失败")
                logger.error(e)
                raise
    """
