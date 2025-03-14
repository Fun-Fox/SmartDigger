import random
import io

from appium import webdriver
from PIL import Image, ImageDraw, ImageColor
import xml.etree.ElementTree as ET
import os
import re
import datetime
import logging
from appium.options.android import UiAutomator2Options
from PIL import ImageFont
from source.services.recorder import Recorder
from .services.vision_model import VisionModelService
from .services.element import ElementManager
from dotenv import load_dotenv

load_dotenv()

__all__ = ['AppiumInspector']


class AppiumInspector:
    def __init__(self, device_name, app_package, app_activity, device_resolution):
        self.device_name = device_name
        self.app_package = app_package
        self.app_activity = app_activity
        self.driver = self._init_driver()
        self.recorder = Recorder()
        self.vision_model_service = VisionModelService()
        self.element_manager = ElementManager(self.recorder, self.driver)
        self.device_resolution = device_resolution

    def _init_driver(self):
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

    def capture_and_mark_elements(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_id = f'{self.device_name}_{timestamp}_{self.app_package}'
        directory_path = os.path.join(os.getenv('SCREENSHOT_DIR'), self.device_name)

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        screenshot = self.driver.get_screenshot_as_png()  # 获取截图二进制数据

        page_source = self.driver.page_source
        root = ET.fromstring(page_source)
        image = Image.open(io.BytesIO(screenshot))  # 转换为 PIL Image 对象
        grayscale_image = image.convert('L')  # 将图像转换为灰度图

        # 保存灰度图
        grayscale_screenshot_path = os.path.join(directory_path, f'{screenshot_id}_grayscale_screenshot.png')
        grayscale_image.save(grayscale_screenshot_path, format='PNG')

        # 重新打开灰度图进行画框
        image = Image.open(grayscale_screenshot_path)
        rgb_image = image.convert('RGB')  # 转换为RGB格式
        draw = ImageDraw.Draw(rgb_image)

        # 检查可点击元素的数量
        is_more_clickable_elements = False
        clickable_elements = [element for element in root.iter() if element.get("clickable") == "true"]
        clickable_elements_limit = 12
        if len(clickable_elements) > clickable_elements_limit:
            logging.info(f"界面可点击元素数量超过{clickable_elements_limit}个，跳过处理")
            is_more_clickable_elements = True

        for i, element in enumerate(root.iter()):
            bounds = element.get('bounds')
            clickable = element.get("clickable")
            if clickable == "true" and bounds:
                if self.recorder.is_record_exist(bounds, screenshot_id):
                    continue
                self.recorder.save_to_db(bounds, screenshot_id, i)
                matches = re.findall(r'\d+', bounds)
                x1, y1, x2, y2 = map(int, matches)
                colors = [
                    "cyan", "magenta", "orange", 'red',
                    "blue", "green", "purple", "pink", "brown",
                    "coral", "navy", "maroon", "olive"
                ]

                color = random.sample(colors, 1)[0]

                # 绘制边框
                draw.rectangle([x1 + 5, y1 + 5, x2 - 5, y2 - 5], outline=color, width=5)

                # 填充框内区域透明图层

                # 绘制文本
                font_path = "fonts/Roboto_SemiCondensed-Black.ttf"
                font = ImageFont.truetype(font_path, size=40)
                text = f"{i}"
                text_mask = font.getmask(text)
                mask_width, mask_height = text_mask.size

                # 优化坐标计算，确保文本和背景框位置准确
                text_x = x2 - mask_width - 30  # 文本起始x坐标，留出10像素边距
                text_y = y1  # 文本起始y坐标，留出10像素边距

                # 绘制文本背景框
                # draw.rectangle([text_x+5 , text_y+5 , text_x + mask_width , text_y + mask_height+10], fill=color)
                # 绘制文本
                draw.text((text_x + 10, text_y), text, fill=color, font=font)

        marked_screenshot_path = os.path.join(directory_path, f'{screenshot_id}_marked_screenshot.jpg')
        rgb_image.save(marked_screenshot_path, quality=85, optimize=True, format='JPEG')  # quality 参数控制压缩质量，范围为 0-100
        self.recorder.generate_markdown()
        print(f"截图已保存至: {os.path.abspath(marked_screenshot_path)}")
        print("Bounds数据已保存至SQLite数据库并生成Markdown文档。")

        return is_more_clickable_elements, os.path.abspath(grayscale_screenshot_path), os.path.abspath(
            marked_screenshot_path)

    def diagnose_and_handle(self, grayscale_screenshot_path, marked_screenshot_path):
        try:

            analysis_result = self.vision_model_service.analyze_screenshot(grayscale_screenshot_path,
                                                                           marked_screenshot_path)
            screenshot_id = self.extract_identifier(marked_screenshot_path)
            if analysis_result.get('popup_exists', False):
                popup_id = analysis_result.get('popup_cancel_button')
                if popup_id:
                    logging.info(f"检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")
                    self.element_manager.click_element_center(popup_id, screenshot_id)
                    self.driver.quit()
                    self.recorder.close()
                else:
                    logging.info("检测到弹窗，但未找到弹窗标识，使用默认方法关闭。")
            else:
                buttons_functions = analysis_result.get('buttons', [])
                print(buttons_functions)
        except Exception as e:
            logging.error(f"诊断过程中发生错误: {e}")

    def extract_identifier(self, screenshot_path: str) -> str:
        """从文件路径中提取标识符部分"""
        filename = os.path.basename(screenshot_path)
        base_name = os.path.splitext(filename)[0]
        return base_name.split('_marked_screenshot')[0]
