import io

from appium import webdriver
from PIL import Image
import xml.etree.ElementTree as ET
import os
import datetime
import logging
from appium.options.android import UiAutomator2Options
from .services.image_processor import ImageProcessor
from .services.vision_model import VisionModelService
from dotenv import load_dotenv

load_dotenv()

__all__ = ['AppiumInspector', 'capture_and_mark_elements', 'diagnose_and_handle']


class AppiumInspector:
    def __init__(self, device_name, app_package, app_activity, device_resolution):
        self.device_name = device_name
        self.app_package = app_package
        self.app_activity = app_activity
        self.device_resolution = device_resolution

    def init_driver(self):
        """初始化Appium驱动"""
        capabilities = {
            'platformName': os.getenv('PLATFORM_NAME'),
            'platformVersion': os.getenv('PLATFORM_VERSION'),
            'appPackage': self.app_package,
            'appActivity': self.app_activity,
            "deviceName": self.device_name,
            "automationName": os.getenv('AUTOMATION_NAME'),
            "appWaitActivity": os.getenv('APP_WAIT_ACTIVITY'),
            "appWaitDuration": int(os.getenv('APP_WAIT_DURATION')),
            "language": os.getenv('LANGUAGE'),
            "uiautomator2ServerInstallTimeout": int(os.getenv('UIAUTOMATOR2_SERVER_INSTALL_TIMEOUT')),
            "skipServerInstallation": os.getenv('SKIP_SERVER_INSTALLATION') == 'True',
            "noReset": os.getenv('NO_RESET') == 'True'
        }
        return webdriver.Remote(os.getenv('APPIUM_SERVER_URL'),
                                options=UiAutomator2Options().load_capabilities(capabilities))


def capture_and_mark_elements(screenshot, device_name, app_package, page_source):
    """捕获并标记元素"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_id = f'{device_name}_{timestamp}_{app_package}'
    directory_path = os.path.join(os.getenv('SCREENSHOT_DIR'), device_name)

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    image = Image.open(io.BytesIO(screenshot))
    image_processor = ImageProcessor()
    # 处理图像
    grayscale_image = image_processor.convert_to_grayscale(image)
    grayscale_screenshot_path = image_processor.save_screenshot(
        grayscale_image, directory_path, screenshot_id, 'grayscale_screenshot')

    # 解析XML并获取元素边界信息

    root = ET.fromstring(page_source)

    # 检查可点击元素的数量
    is_more_clickable_elements = False
    clickable_elements = [element for element in root.iter() if element.get("clickable") == "true"]
    print(clickable_elements)
    clickable_elements_bounds_list = [(elements.get('bounds'), i) for i, elements in enumerate(clickable_elements)
                                      if
                                      elements.get('bounds')]
    print(clickable_elements_bounds_list)

    clickable_elements_limit = 12
    if len(clickable_elements) > clickable_elements_limit:
        logging.info(f"界面可点击元素数量超过{clickable_elements_limit}个，跳过处理")
        is_more_clickable_elements = True

    # 重新打开灰度图进行画框
    image = Image.open(grayscale_screenshot_path)
    rgb_image = image.convert('RGB')  # 转换为RGB格式

    # 绘制元素边框
    marked_screenshot_path, single_color_screenshot_path = image_processor.draw_element_borders(rgb_image,
                                                                                                clickable_elements_bounds_list,
                                                                                                screenshot_id,
                                                                                                directory_path)
    logging.info(f"截图已保存至: {os.path.abspath(marked_screenshot_path)}")

    return screenshot_id, is_more_clickable_elements, os.path.abspath(grayscale_screenshot_path), os.path.abspath(
        marked_screenshot_path), os.path.abspath(single_color_screenshot_path)


def diagnose_and_handle(grayscale_screenshot_path, marked_screenshot_path, ):
    try:
        vision_model_service = VisionModelService()
        analysis_result = vision_model_service.analyze_screenshot(grayscale_screenshot_path,
                                                                  marked_screenshot_path)
        if analysis_result.get('popup_exists', False):
            popup_id = analysis_result.get('popup_cancel_button')
            if popup_id:
                return popup_id

            else:
                logging.info("检测到弹窗，但未找到弹窗标识，使用默认方法关闭。")
        else:
            logging.info("未检测到弹窗")
    except Exception as e:
        logging.error(f"诊断过程中发生错误: {e}")
