import logging
from PIL import Image

from source import capture_and_mark_elements, diagnose_and_handle
from source.api.utils.template_matcher import TemplateMatcher
from source.services import ElementManager
from source.services.vision_model import VisionModelService
from source.services.image_processor import ImageProcessor
from source.services.recorder import Recorder  # 添加 Recorder 导入

logger = logging.getLogger(__name__)


class DiagnosisService:
    def __init__(self):
        self.vision_model = VisionModelService()
        self.template_matcher = TemplateMatcher()
        self.image_processor = ImageProcessor()
        self.recorder = Recorder()  # 初始化 Recorder
        self.known_popups = {}

    def diagnose(self, screenshot_path, xml_path, device_name):
        """
        执行诊断
        :param screenshot_path: 截图路径
        :param xml_path: XML文件路径
        :param device_name: 设备名称
        :return: 诊断结果
        """
        # 1. 先进行模板匹配
        page_source = xml_path
        app_package = 'api'

        with open(screenshot_path, 'rb') as f:
            image = Image.open(f)

        # 2. 处理图片
        try:
            # 初始化 Appium Inspector
            # 获取截图
            recorder = Recorder()
            element_manager = ElementManager(recorder)
            # 生成 markdown
            recorder.generate_markdown()
            # 进行元素定位
            (screenshot_id, is_more_clickable_elements, grayscale_screenshot_path,
             marked_screenshot_path, single_color_screenshot_path) = capture_and_mark_elements(
                image, device_name, app_package, page_source)
            # 进行弹窗识别
            if not is_more_clickable_elements:
                # 进行弹窗识别
                popup_id = diagnose_and_handle(grayscale_screenshot_path, marked_screenshot_path)

                logging.info(f"检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")
                # 获取弹窗中心点
                center_x, center_y = element_manager.element_center(single_color_screenshot_path,
                                                                    popup_id, screenshot_id)
                # 点击弹窗
                logging.info(f"弹窗关闭成功")

                recorder.close()
            logging.info(f"运行结束")
        except Exception as e:
            logging.error(f"运行 Appium Inspector 时发生错误: {e}")
            raise e
