from appium import webdriver
from PIL import Image
import os
import datetime
from appium.options.android import UiAutomator2Options
from .services.image_processor import ImageProcessor
from .services.vision_model import VisionModelService
from dotenv import load_dotenv
from source.utils.log_config import setup_logger

logger = setup_logger(__name__)
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


def capture_and_mark_elements(screenshot_image, device_name, app_package, clickable_elements) -> tuple[
                                                                                                     str, bool, None, None] | \
                                                                                                 tuple[
                                                                                                     str, bool, Image, Image]:
    # """捕获并标记元素"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    device_name = device_name.replace(':', '_')
    # 兼容特殊情况
    screenshot_id = f'{device_name}_{timestamp}_{app_package}'

    image_processor = ImageProcessor()

    # 处理图像
    grayscale_image = image_processor.convert_to_grayscale(screenshot_image)
    # logger.info(f"图像已转换为灰度图像")

    # clickable_elements = [element for element in xml_root.iter() if element.get("clickable") == "true"]
    clickable_elements_bounds_list = [(elements.get('bounds'), i) for i, elements in enumerate(clickable_elements)
                                      if elements.get('bounds')]

    clickable_elements_limit = 12
    if len(clickable_elements) > clickable_elements_limit:
        logger.info(f"界面可点击元素数量超过{clickable_elements_limit}个，跳过处理")
        return screenshot_id, True, None, None

    # 绘制元素边框
    # logger.info(f"调用多次？")
    marked_screenshot_image, non_clickable_area_image = image_processor.draw_element_borders(
        grayscale_image,  # 直接使用灰度图像
        clickable_elements_bounds_list,
        screenshot_id
    )
    # logger.info(f"截图已保存至: {os.path.abspath(marked_screenshot_path)}")

    return screenshot_id, False, marked_screenshot_image, non_clickable_area_image


def diagnose_and_handle(marked_screenshot_image, ):
    try:
        vision_model_service = VisionModelService()

        analysis_result = vision_model_service.analyze_screenshot(
            marked_screenshot_image)
        logger.info(f'视觉分析结果:{analysis_result}')
        if analysis_result.get('popup_exists', False):
            popup_id = analysis_result.get('popup_cancel_button')
            if popup_id:

                return popup_id
            else:
                logger.info("检测到弹窗，但未找到弹窗标识，使用默认方法关闭。")
                return None
        else:
            logger.info("未检测到弹窗")
            return None
    except Exception as e:
        logger.error(f"诊断过程中发生错误: {e}")
        raise e
