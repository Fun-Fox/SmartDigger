import uuid
from flask import Flask, request, jsonify, g
from .services import vision_analysis, lvm_analysis
from dotenv import load_dotenv
import base64
from source.utils.log_config import setup_logger

logger = setup_logger(__name__)
load_dotenv()

app = Flask(__name__)
__all__ = ['app']

# 定义接口的必填参数
# REQUIRED_PARAMS = ['screenshot', 'xml_file', 'devices_name','resolution']
REQUIRED_PARAMS = ['screenshot']


@app.after_request
def set_content_type(response):
    """设置响应头为JSON格式"""
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


@app.before_request
def before_request():
    """为每个请求生成唯一的 trace_id"""
    g.trace_id = str(uuid.uuid4())


@app.route('/api/v1/diagnose', methods=['POST'])
def diagnose():
    """
    诊断接口
    请求参数 (JSON):
    - screenshot: Base64 编码的手机屏幕截图 (必填)
    - xml_file: XML层级结构文本 (必填)
    - devices_name: 设备名称 (必填)
    返回结果:
    - 诊断分析结果JSON
    """
    try:
        # 获取 JSON 数据
        data = request.json
        if not data:
            logger.error("请求体为空")
            return jsonify({"msg": "请求体为空，请提供有效的JSON数据"}), 400

        # 检查必填参数是否缺失
        missing_params = [param for param in REQUIRED_PARAMS if param not in data]
        if missing_params:
            logger.error(f"必填参数缺失: {', '.join(missing_params)}")
            return jsonify({"msg": f"必填参数缺失: {', '.join(missing_params)}"}), 400

        # 校验必填参数是否为空
        empty_params = [param for param in REQUIRED_PARAMS if not data.get(param)]
        if empty_params:
            logger.error(f"必填参数为空: {', '.join(empty_params)}")
            return jsonify({"msg": f"必填参数为空: {', '.join(empty_params)}"}), 400

        # 解码 Base64 图像
        try:
            screenshot_bytes = base64.b64decode(data['screenshot'])
        except Exception as e:
            logger.error(f"Base64 解码失败: {str(e)}")
            return jsonify({"msg": "图片Base64 解码失败，请检查图片格式是否正确"}), 400

        # 调用诊断服务
        try:
            if data['resolution'] != '':
                center_x, center_y = lvm_analysis(
                    # todo 将screenshot_bytes 转为灰度图像，并且存储到本地
                    # todo 分辨率的传输
                    screenshot_bytes, data['resolution'], data['devices_name']
                )

            else:
                center_x, center_y = vision_analysis(
                    screenshot_bytes, data['xml_file'], data['devices_name']
                )
            if center_x is None or center_y is None:
                logger.info("系统诊断为非弹窗，麻烦人工排查")
                return jsonify({"msg": "系统诊断为非弹窗，麻烦人工排查"}), 500

            logger.info(f"视觉诊断结果: ({center_x}, {center_y})")
            return jsonify({
                "msg": f"视觉诊断为弹窗，跳过的坐标为: ({center_x}, {center_y})",
                "script": adb_tap_code(data['devices_name'], center_x, center_y).strip()
            }), 200

        except Exception as e:
            logger.error(f"诊断服务调用失败: {str(e)}")
            return jsonify({"msg": "诊断服务调用失败，请稍后重试"}), 500

    except Exception as e:
        logger.error(f"诊断失败: {str(e)}")
        return jsonify({"msg": f"系统异常: {str(e)}"}), 500


def adb_tap_code(device_name, x, y) -> str:
    return f"""import subprocess;subprocess.run( ['adb', '-s', {device_name}, 'shell', 'input', 'tap', str({x}), str({y})],check=True) """
