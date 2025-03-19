from datetime import datetime

from flask import Flask, request, jsonify
from source.api.services.diagnosis_service import DiagnosisService
import logging
from dotenv import load_dotenv
import os
import base64

load_dotenv()

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

diagnosis_service = DiagnosisService()


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
            return jsonify({"error": "请求参数缺失"}), 400

        # 校验 screenshot 和 xml_file 是否为空
        if not data['screenshot'] or not data['xml_file']:
            logger.error("screenshot 或 xml_file 为空")
            return jsonify({"error": "screenshot 或 xml_file 为空"}), 400

        # 解码 Base64 图像
        screenshot_base64 = data['screenshot']
        try:
            screenshot_bytes = base64.b64decode(screenshot_base64)
        except Exception as e:
            logger.error(f"Base64 解码失败: {str(e)}")
            return jsonify({"error": "Base64 解码失败"}), 400

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
            return jsonify({"error": "保存截图失败"}), 500

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
            return jsonify({"error": "保存 XML 文件失败"}), 500

        # 调用诊断服务
        try:
            result = diagnosis_service.diagnose(screenshot_path, xml_path, device_name)
            logger.info("诊断成功")
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"诊断服务调用失败: {str(e)}")
            return jsonify({"error": "诊断服务调用失败"}), 500

    except Exception as e:
        logger.error(f"诊断失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
