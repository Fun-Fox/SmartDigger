import os
import xml.etree.ElementTree as ET

from lxml import etree

from source import capture_and_mark_elements, diagnose_and_handle
from source.api.utils.template_matcher import TemplateMatcher
from source.services import ElementManager
from source.services.recorder import Recorder
from source.utils.log_config import setup_logger
import io
from PIL import Image
import xml.etree.ElementTree as ET

logger = setup_logger(__name__)
__all__ = ['vision_analysis']


def vision_analysis(screenshot_bytes, xml_page_struct, device_name, ):
    """
    执行诊断
    :param screenshot_path: 截图路径
    :param xml_path: XML文件路径
    :param device_name: 设备名称
    :return: 诊断结果
    """
    # with open(screenshot_path, 'rb') as f:
    #     image = f.read()
    # with open(xml_path, 'rb') as f:
    #     page_source = f.read()
    # 预留参数app_package
    app_package = 'api'
    # 进行元素定位，图像处理，解析xml数据存于数据库
    # 解析XML并获取元素边界信息
    # todo 优化xml解析性能优化

    screenshot_image = Image.open(io.BytesIO(screenshot_bytes))

    try:
        xml_root = etree.fromstring(xml_page_struct)
        clickable_elements = xml_root.xpath(".//*[@clickable='true']")
    except Exception as e:
        logger.error(f"XML 格式错误: {str(e)}")
        raise e

    screenshot_id, is_more_clickable_elements, marked_screenshot_image, non_clickable_area_image = capture_and_mark_elements(
        screenshot_image, device_name, app_package, clickable_elements)

    try:
        logger.info('开始进行模板匹配...')
        # 1. 先进行模板匹配
        template_matcher = TemplateMatcher()
        is_template_match, template_file = template_matcher.match_known_popups(non_clickable_area_image)
        logger.info(f'模板匹配结果: {is_template_match}, 模板文件: {template_file}')
    except Exception as e:
        logger.error(f"模板匹配时发生错误: {e}")
        raise e

    try:
        recorder = Recorder()
        if is_template_match:
            center_x, center_y = recorder.get_template_center_point(template_file.rstrip('.jpeg'))
            if center_x is not None or center_y is not None:
                recorder.close()
                logger.info("模版匹配成功，查询模版匹配坐标为：" + str(center_x) + "," + str(center_y))
                return center_x, center_y
            logger.info("模版匹配成功，查询模版匹配坐标数据不存在")
            # 异常情况-备用路线
            return popup_analysis(recorder, is_more_clickable_elements,
                                  marked_screenshot_image, non_clickable_area_image, screenshot_id)
        else:
            # 去调用视觉API判断模版对应的内容
            return popup_analysis(recorder, is_more_clickable_elements,
                                  marked_screenshot_image, non_clickable_area_image, screenshot_id)

    except Exception as e:
        raise e


# 获取当前脚本的绝对路径
current_file_path = os.path.abspath(__file__)
# 推导项目根目录（假设项目根目录是当前脚本的祖父目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))


def popup_analysis(recorder, is_more_clickable_elements, marked_screenshot_image, non_clickable_area_image,
                   screenshot_id):
    try:

        center_x, center_y = None, None
        if not is_more_clickable_elements:
            # 进行弹窗识别
            popup_id = diagnose_and_handle(marked_screenshot_image)
            if popup_id is not None and popup_id > 0:
                logger.info(f"视觉模型检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")
                # 获取弹窗中心点
                element_manager = ElementManager(recorder)
                center_x, center_y = element_manager.element_center(popup_id, screenshot_id)

        # 保存图像
        device_name = screenshot_id.split('_')[0]
        directory_path = os.path.join(project_root, os.getenv('SCREENSHOT_DIR'), device_name)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        template_dir = os.path.join(project_root, os.getenv('TEMPLATE_DIR'))
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)

        # 异步保存图像
        save_images_async(marked_screenshot_image, non_clickable_area_image, directory_path, template_dir,
                          screenshot_id, recorder, center_x, center_y)
        return center_x, center_y
    except Exception as e:
        logger.error(f"运行视觉模型定位时发生错误: {e}")
        recorder.close()
        raise e


import threading


def save_images_async(marked_screenshot_image, non_clickable_area_image, directory_path, template_dir, screenshot_id,
                      recorder, center_x, center_y):
    """异步保存图像的线程函数"""

    def save():
        # 保存标记后的截图
        save_screenshot(marked_screenshot_image, directory_path, screenshot_id + '_marked_screenshot', format='JPEG')

        # 保存模板信息
        if center_x is not None and center_y is not None:
            # 保存不可点击区域的截图
            template_path = os.path.join(template_dir, f"{screenshot_id}.jpeg")
            save_screenshot(non_clickable_area_image, template_path, screenshot_id, format='JPEG')
            recorder.save_template(screenshot_id, center_x, center_y)
        recorder.close()

    # 启动线程
    thread = threading.Thread(target=save)
    thread.start()


def save_screenshot(image, directory_path, screenshot_id, format='JPEG'):
    """保存截图到指定路径"""
    screenshot_path = os.path.join(directory_path, f'{screenshot_id}.{format.lower()}')
    image.save(directory_path, format=format, quality=85)
    return screenshot_path
