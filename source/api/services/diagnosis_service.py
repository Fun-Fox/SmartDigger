import logging
from PIL import Image

from source import capture_and_mark_elements, diagnose_and_handle
from source.api.utils.template_matcher import TemplateMatcher
from source.services import ElementManager
from source.services.recorder import Recorder  # 添加 Recorder 导入

logger = logging.getLogger(__name__)
__all__ = ['vision_analysis']


def vision_analysis(screenshot_path, xml_path, device_name, ):
    """
    执行诊断
    :param screenshot_path: 截图路径
    :param xml_path: XML文件路径
    :param device_name: 设备名称
    :return: 诊断结果
    """
    # 1. 先进行模板匹配
    template_matcher = TemplateMatcher()
    try:
        is_template_match, template_file = template_matcher.match_known_popups(screenshot_path)
        logging.info(f'模板匹配结果: {is_template_match}, 模板文件: {template_file}')
    except Exception as e:
        logging.error(f"模板匹配时发生错误: {e}")
        raise e

    recorder = Recorder()
    if is_template_match:
        center_x, center_y = recorder.get_template_center_point(template_file.rstrip('.png'))
        recorder.close()
        return center_x, center_y
    else:
        page_source = xml_path
        # 预留参数app_package
        app_package = 'api'
        with open(screenshot_path, 'rb') as f:
            image = Image.open(f)
        # 2. 处理图片
        try:
            # 获取截图
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
                popup_id = diagnose_and_handle(grayscale_screenshot_path,
                                               marked_screenshot_path)
                if popup_id is not None and popup_id > 0:
                    logging.info(f"视觉模型检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")
                    # 获取弹窗中心点
                    center_x, center_y = element_manager.element_center(single_color_screenshot_path,
                                                                        popup_id, screenshot_id)
                    recorder.close()
                    return center_x, center_y
        except Exception as e:
            logging.error(f"运行视觉模型定位时发生错误: {e}")
            recorder.close()
            raise e
