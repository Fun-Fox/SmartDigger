from source import capture_and_mark_elements, diagnose_and_handle
from source.api.utils.template_matcher import TemplateMatcher
from source.services import ElementManager
from source.services.recorder import Recorder
from source.utils.log_config import setup_logger

logger = setup_logger(__name__)
__all__ = ['vision_analysis']


def vision_analysis(screenshot_path, xml_path, device_name, ):
    """
    执行诊断
    :param screenshot_path: 截图路径
    :param xml_path: XML文件路径
    :param device_name: 设备名称
    :return: 诊断结果
    """
    with open(screenshot_path, 'rb') as f:
        image = f.read()
    with open(xml_path, 'rb') as f:
        page_source = f.read()
    # 预留参数app_package
    app_package = 'api'

    # 进行元素定位，图像处理
    screenshot_id, is_more_clickable_elements, grayscale_screenshot_path, marked_screenshot_path, single_color_screenshot_path = capture_and_mark_elements(
        image, device_name, app_package, page_source)

    try:
        logger.info('开始进行模板匹配...')
        # 1. 先进行模板匹配
        template_matcher = TemplateMatcher()
        is_template_match, template_file = template_matcher.match_known_popups(single_color_screenshot_path)
        logger.info(f'模板匹配结果: {is_template_match}, 模板文件: {template_file}')
    except Exception as e:
        logger.error(f"模板匹配时发生错误: {e}")
        raise e

    recorder = Recorder()
    try:
        if is_template_match:
            center_x, center_y = recorder.get_template_center_point(template_file.rstrip('.jpeg'))
            if center_x is not None or center_y is not None:
                recorder.close()
                logger.info("模版匹配成功，查询模版匹配坐标为：" + str(center_x) + "," + str(center_y))
                return center_x, center_y
            logger.info("模版匹配成功，查询模版匹配坐标数据不存在")
            return popup_analysis(recorder, is_more_clickable_elements, grayscale_screenshot_path,
                                  marked_screenshot_path, single_color_screenshot_path, screenshot_id)
        else:
            return popup_analysis(recorder, is_more_clickable_elements, grayscale_screenshot_path,
                                  marked_screenshot_path, single_color_screenshot_path, screenshot_id)

    except Exception as e:
        raise e


def popup_analysis(recorder, is_more_clickable_elements, grayscale_screenshot_path, marked_screenshot_path,
                   single_color_screenshot_path, screenshot_id):
    try:
        # 处理图片
        # 获取截图
        element_manager = ElementManager(recorder)

        # 生成 markdown
        recorder.generate_markdown()
        # 进行弹窗识别
        if not is_more_clickable_elements:
            # 进行弹窗识别
            popup_id = diagnose_and_handle(grayscale_screenshot_path,
                                           marked_screenshot_path)
            if popup_id is not None and popup_id > 0:
                logger.info(f"视觉模型检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")
                # 获取弹窗中心点
                center_x, center_y = element_manager.element_center(single_color_screenshot_path,
                                                                    popup_id, screenshot_id)
                recorder.close()
                return center_x, center_y
            else:
                return None, None
        else:
            return None, None
    except Exception as e:
        logger.error(f"运行视觉模型定位时发生错误: {e}")
        recorder.close()
        raise e
