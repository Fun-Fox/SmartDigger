import json
import os
import requests
from base64 import b64encode
from dotenv import load_dotenv
from typing import Dict, Any
import logging

load_dotenv()


class VisionModelService:
    """A service for interacting with the vision model API to analyze screenshots."""

    # Constants
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # in seconds
    DEFAULT_MODEL = "deepseek-ai/deepseek-vl2"

    def __init__(self):
        """Initialize the vision model service with API configurations."""
        self.api_url = self._get_api_url()
        self.api_key = self._get_api_key()
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _get_api_url() -> str:
        """Get the vision model API URL from environment variables."""
        url = os.getenv('VISION_MODEL_API_URL')
        if not url:
            raise ValueError("Vision model API URL is not configured")
        return url

    @staticmethod
    def _get_api_key() -> str:
        """Get the vision model API key from environment variables."""
        key = os.getenv('VISION_MODEL_API_KEY')
        if not key:
            raise ValueError("Vision model API key is not configured")
        return key

    def _handle_response_errors(self, response_json: Dict) -> None:
        """Handle errors returned by the vision model API.
        
        Args:
            response_json: The JSON response from the API.
            
        Raises:
            Exception: If the response contains an error code or message.
        """
        if 'code' in response_json:
            error_code = response_json['code']
            error_message = response_json.get('message', 'Unknown error')
            if error_code == 20012:
                self.logger.error(f"Vision model exception: {error_message}")
                raise Exception(f"视觉模型返回异常: {error_message}")
            elif error_code == 50505:
                self.logger.error(f"Vision model service overload: {error_message}")
                raise Exception(f"视觉模型服务过载: {error_message}")

        if 'message' in response_json and "rate limiting" in response_json['message']:
            error_message = response_json['message']
            self.logger.error(f"Rate limit exceeded: {error_message}")
            raise Exception(f"请求被拒绝，达到速率限制: {error_message}")

    def analyze_screenshot(self, grayscale_screenshot_path: str, marked_screenshot_path: str) -> Dict[str, Any]:
        """Analyze a screenshot using the vision model API.
        
        Args:
            grayscale_screenshot_path: Path to the screenshot image file.
            
        Returns:
            A dictionary containing the analysis results.
            
        Raises:
            Exception: If the analysis fails or the response cannot be parsed.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                with open(grayscale_screenshot_path, "rb") as image_file:
                    screenshot_base64 = b64encode(image_file.read()).decode('utf-8')

                with open(marked_screenshot_path, "rb") as image_file:
                    marked_screenshot_base64 = b64encode(image_file.read()).decode('utf-8')

                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                }

                payload = self._build_payload(screenshot_base64, marked_screenshot_base64)
                response = requests.post(self.api_url, json=payload, headers=headers)
                print(response.json())
                if response.status_code == 200:
                    return self._process_response(response.json())

                self.logger.warning(f"Attempt {attempt + 1} failed with status code {response.status_code}")

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.MAX_RETRIES - 1:
                    self.logger.error("All attempts failed")
                    raise Exception(f"Failed to analyze screenshot after {self.MAX_RETRIES} attempts: {str(e)}")

        raise Exception("Unexpected error in analyze_screenshot")

    def _build_payload(self, screenshot_base64, marked_screenshot_base64) -> Dict:
        """Build the API request payload."""
        return {
            "model": self.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        # {
                        #     "type": "image_url",
                        #     "image_url": {
                        #         "url": f"data:image/jpeg;base64,{screenshot_base64}",
                        #         "detail": "low"
                        #     }
                        # },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{marked_screenshot_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": self._build_analysis_prompt()
                        }

                    ]
                }
            ],
            "stream": False
        }

    @staticmethod
    def _build_analysis_prompt() -> str:
        """Build the analysis prompt for the vision model."""
        return '''
        请以严格JSON格式返回以下分析结果，不要包含任何额外文本：
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

    def _process_response(self, response_json: Dict) -> Dict:
        """Process the API response and extract the analysis results."""
        self._handle_response_errors(response_json)

        # 新增：直接解析顶层JSON结构
        if 'choices' in response_json and response_json['choices']:
            choice = response_json['choices'][0]
            content = choice.get('message', {}).get('content', {})
            if isinstance(content, str):
                try:
                    return json.loads(content)  # 假设响应内容直接是JSON字符串
                except json.JSONDecodeError as e:
                    raise Exception(f"Invalid JSON format: {str(e)}")
            else:
                raise Exception("Expected JSON content not found in response")
        raise Exception("Failed to parse the response from the vision model")
