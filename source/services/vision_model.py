import json
import os
from io import BytesIO

import requests
from base64 import b64encode

from PIL import Image
from dotenv import load_dotenv
from typing import Dict, Any
from source.utils.log_config import setup_logger

load_dotenv()


class VisionModelService:
    """用于与视觉模型API交互，分析截图的工具类。"""

    # 常量
    MAX_RETRIES = 1
    RETRY_DELAY = 1  # 重试延迟，单位：秒
    # DEFAULT_MODEL = "deepseek-ai/deepseek-vl2"
    DEFAULT_MODEL = "Qwen/Qwen2.5-VL-32B-Instruct"

    # DEFAULT_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
    # DEFAULT_MODEL = "Pro/Qwen/Qwen2.5-VL-7B-Instruct"

    def __init__(self, screen_resolution=""):
        """初始化视觉模型服务，配置API信息。"""

        self.api_url = self._get_api_url()
        self.api_key = self._get_api_key()
        self.logger = setup_logger(__name__)
        self.screen_resolution = screen_resolution

    @staticmethod
    def _get_api_url() -> str:
        """从环境变量中获取视觉模型API的URL。"""
        url = os.getenv('VISION_MODEL_API_URL')
        if not url:
            raise ValueError("未配置视觉模型API的URL")
        return url

    @staticmethod
    def _get_api_key() -> str:
        """从环境变量中获取视觉模型API的密钥。"""
        key = os.getenv('VISION_MODEL_API_KEY')
        if not key:
            raise ValueError("未配置视觉模型API的密钥")
        return key

    def _handle_response_errors(self, response_json: Dict) -> None:
        """处理视觉模型API返回的错误。

        Args:
            response_json: API返回的JSON响应。

        Raises:
            Exception: 如果响应中包含错误码或错误信息。
        """
        if 'code' in response_json:
            error_code = response_json['code']
            error_message = response_json.get('message', '未知错误')
            if error_code == 20012:
                self.logger.error(f"视觉模型异常: {error_message}")
                raise Exception(f"视觉模型返回异常: {error_message}")
            elif error_code == 50505:
                self.logger.error(f"视觉模型服务过载: {error_message}")
                raise Exception(f"视觉模型服务过载: {error_message}")

        if 'message' in response_json and "rate limiting" in response_json['message']:
            error_message = response_json['message']
            self.logger.error(f"达到速率限制: {error_message}")
            raise Exception(f"请求被拒绝，达到速率限制: {error_message}")

    def analyze_screenshot(self, marked_screenshot_image):
        """使用视觉模型API分析截图。

        Args:
            marked_screenshot_image: 截图文件路径或PIL.Image对象。

        Returns:
            包含分析结果的字典。

        Raises:
            Exception: 如果分析失败或无法解析响应。
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # 将截图转换为Base64编码
                marked_screenshot_base64 = self.convert_image_to_base64(marked_screenshot_image)
                # raise Exception("analyze_screenshot 方法中发生意外错误")

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }
                # 构建请求负载
                payload = self._build_payload(marked_screenshot_base64)
                # 打印格式化请求内容
                # self.logger.info("发送请求到视觉模型API:")
                # self.logger.info(f"URL: {self.api_url}")
                # self.logger.info(f"Headers: {json.dumps(headers, indent=2)}")
                # self.logger.info(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
                response = requests.post(self.api_url, json=payload, headers=headers)
                # 打印格式化响应内容
                self.logger.info(f"收到视觉模型API响应:{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
                # self.logger.info(f"Status Code: {response.status_code}")
                # 处理响应
                if response.status_code == 200:
                    if response.json().get("content") == "":
                        raise Exception("视觉模型返回空结果")
                    return self._process_response(response.json())

                self.logger.warning(f"第 {attempt + 1} 次尝试失败，状态码: {response.status_code}")

            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    self.logger.error("所有尝试均失败")
                    raise Exception(f"分析截图失败，尝试 {self.MAX_RETRIES} 次后仍未成功: {str(e)}")

        raise Exception("analyze_screenshot 方法中发生意外错误")

    @staticmethod
    def convert_image_to_base64(marked_screenshot_image, quality=80) -> str:
        """将截图转换为Base64编码，并降低图像质量以减小数据大小。

        Args:
            marked_screenshot_image: 截图文件路径或PIL.Image对象。
            quality: 图像质量，范围是 1-100，默认值为 50。

        Returns:
            Base64编码的字符串。
        """

        # 创建字节流对象
        byte_stream = BytesIO()

        # 将图像保存到字节流，降低质量
        marked_screenshot_image.save(byte_stream, format='JPEG', quality=quality)

        # 保存字节流为图片文件，用于验证效果
        # save_path = "D:\\Code\\SmartDigger\\template\\temp_saved.jpg"
        # with open(save_path, "wb") as f:
        #     f.write(byte_stream.getvalue())
        # self.logger.info(f"图像已保存到: {save_path}")

        # 获取字节数据
        image_bytes = byte_stream.getvalue()

        # 将字节数据编码为 Base64
        base64_bytes = b64encode(image_bytes)

        # 解码为 UTF-8 字符串
        base64_str = base64_bytes.decode('utf-8')

        return base64_str

    def _build_payload(self, marked_screenshot_base64) -> Dict:
        """构建API请求负载。

        Args:
            marked_screenshot_base64: Base64编码的截图。

        Returns:
            请求负载的字典。
        """
        return {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{marked_screenshot_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": self._build_analysis_prompt() if self.screen_resolution == '' else self._build_analysis_prompt_co(
                                self.screen_resolution)
                        }
                    ]
                }
            ],
            "stream": False
        }

    @staticmethod
    def _build_analysis_prompt() -> str:
        """构建视觉模型的分析提示。

        Returns:
            分析提示的字符串。
        """
        return '''
        请以严格以JSON格式返回以下分析结果，不要包含任何额外文本：
        {
            "popup_exists": true/false,
            "popup_cancel_button": 数字标记（若无则填null）
        }

        分析要求：
        1. 判断手机页面是否存在弹框（popup_exists）。弹框通常是一个覆盖在主界面上的小窗口或对话框。
        2. 若存在弹窗，找到关闭/忽略/取消操作按钮的数字标记。这些按钮通常用于关闭弹框。
        3. 请仔细区分弹框和主界面元素，确保不会将主界面误判为弹框。

        示例：
        - 如果页面中有一个覆盖在主界面上的小窗口，且该窗口有一个“取消”按钮，则返回：
          {
              "popup_exists": true,
              "popup_cancel_button": 1
          }
        - 如果页面中没有弹框，则返回：
          {
              "popup_exists": false,
              "popup_cancel_button": null
          }
        '''

    @staticmethod
    def _build_analysis_prompt_co(screen_resolution) -> str:
        return f'''
        请以严格JSON格式返回以下分析结果，不要包含任何额外文本，非Markdown文本：
        {{
            "popup_exists": true/false,
            "button_coordinates": {{
                "x": 按钮中心的x坐标,
                "y": 按钮中心的y坐标
            }}
        }}
        当前分辨率为{screen_resolution}，请根据该分辨率进行分析。
        分析要求：
        1. 判断手机页面是否存在弹框（popup_exists）。
        2. 若存在弹框，找到弹窗上的关闭/忽略/取消操作按钮（这些按钮通常用于关闭弹框）
        3. 请根据手机分辨率，返回按钮中心的手机屏幕x坐标和y坐标。

        示例：
        - 如果页面中有一个覆盖在主界面上的小窗口，且该窗口有一个“取消”按钮，取消按钮的坐标为（100,200）则返回：
          {{
              "popup_exists": true,
              "button_coordinates": {{
                  "x": 100,
                  "y": 200
              }}
          }}
        - 如果页面中没有弹框，则返回：
          {{
              "popup_exists": false,
              "button_coordinates": null
          }}
        '''

    def _process_response(self, response_json: Dict) -> Dict:
        """处理API响应并提取分析结果。

        Args:
            response_json: API返回的JSON响应。

        Returns:
            分析结果的字典。

        Raises:
            Exception: 如果无法解析响应。
        """
        self._handle_response_errors(response_json)

        # 解析顶层JSON结构
        if 'choices' in response_json and response_json['choices']:
            choice = response_json['choices'][0]
            content = choice.get('message', {}).get('content', {})
            if isinstance(content, str):
                try:
                    if content.startswith('```json'):
                        content = content[7:]
                        if content.endswith('```'):
                            content = content[:-3]
                            return json.loads(content)
                    return json.loads(content)  # 假设响应内容直接是JSON字符串
                except json.JSONDecodeError as e:
                    raise Exception(f"无效的JSON格式: {str(e)}")
            else:
                raise Exception("未在响应中找到预期的JSON内容")
        raise Exception("无法解析视觉模型的响应")
