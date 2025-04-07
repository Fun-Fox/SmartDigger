"""
主入口模块

模块职责：
- 程序启动
- 日志配置
- 设备信息获取
- 主流程控制
"""
import io

from PIL import Image
from lxml import etree

from source import AppiumInspector, capture_and_mark_elements, diagnose_and_handle
from source.api.services import lvm_analysis
from source.services import ElementManager, click_element_close
from source.tools import AdbHelper
from dotenv import load_dotenv

from source.services.recorder import Recorder
from source.utils.log_config import setup_logger

logger = setup_logger(__name__)

# 加载环境变量
load_dotenv()


def run_appium_inspector(device_name, app_package, app_activity, device_resolution):
    """运行 Appium Inspector 进行应用界面分析
    
    参数:
        device_name: 设备名称
        app_package: 当前应用包名
        app_activity: 当前应用活动
        device_resolution: 设备分辨率
        
    异常:
        ValueError: 当必要参数为空时抛出
    """
    if not all([device_name, app_package, app_activity, device_resolution]):
        logger.error("无效的输入参数：device_name、app_package 或 app_activity 为空。")
        raise ValueError("device_name、app_package 和 app_activity 必须为非空字符串。")

    try:
        # 初始化 Appium Inspector
        driver = AppiumInspector(device_name, app_package, app_activity, device_resolution).init_driver()

        # 获取截图
        screenshot = driver.get_screenshot_as_png()
        xml_page_struct = driver.page_source

        recorder = Recorder()
        element_manager = ElementManager(recorder)

        screenshot_image = Image.open(io.BytesIO(screenshot))

        try:
            xml_page_bytes = xml_page_struct.encode('utf-8')
            xml_root = etree.fromstring(xml_page_bytes)
            clickable_elements = xml_root.xpath(".//*[@clickable='true']")
        except Exception as e:
            logger.error(f"XML 格式错误: {str(e)}")
            raise e

        # 进行元素定位
        screenshot_id, is_more_clickable_elements, marked_screenshot_image, non_clickable_area_image = capture_and_mark_elements(
            screenshot_image, device_name, app_package, clickable_elements)

        # 进行弹窗识别
        if not is_more_clickable_elements:

            if not isinstance(marked_screenshot_image, Image.Image):
                raise ValueError("输入必须是 PIL.Image.Image 对象")
                # 如果图像是 RGBA 模式，转换为 RGB 模式
            if marked_screenshot_image.mode == 'RGBA':
                marked_screenshot_image = marked_screenshot_image.convert('RGB')

            # 进行弹窗识别
            popup_id = diagnose_and_handle(marked_screenshot_image)
            logger.info(f"弹窗标识为: {popup_id}")
            # 获取弹窗中心点
            if popup_id is not None and popup_id > 0:
                center_x, center_y = element_manager.element_center(popup_id, screenshot_id)
                # 点击弹窗
                logger.info(f"检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")

                click_element_close(driver, center_x, center_y)
                logger.info(f"坐标为: {center_x},{center_y}")
            logger.info(f"弹窗关闭成功")
            driver.quit()
            recorder.close()
        logger.info(f"运行结束")
    except Exception as e:
        logger.error(f"运行 Appium Inspector 时发生错误: {e}")
        raise


def run_appium_inspector_by_lvm(device_name, app_package, app_activity, device_resolution):
    driver = AppiumInspector(device_name, app_package, app_activity, device_resolution).init_driver()

    # 获取截图
    screenshot = driver.get_screenshot_as_png()

    center_x, center_y = lvm_analysis(screenshot_bytes=screenshot, screen_resolution=device_resolution,
                                      device_name=device_name)
    if center_x is not None and center_y is not None:
        logger.info(f"坐标为: {center_x},{center_y}")
        click_element_close(driver, center_x, center_y)
    else:
        logger.info(f"没有找到弹窗")


def main():
    """主函数，获取设备信息并运行 Appium Inspector"""
    try:
        # 获取设备信息
        adb = AdbHelper()
        device_name = adb.get_device_name()
        app_package = adb.get_current_app_package()
        print(f"当前应用包名：{app_package}")
        app_activity = adb.get_current_app_activity()
        print(f"当前应用活动：{app_activity}")
        device_resolution = adb.get_device_resolution()
        print(f"设备分辨率：{device_resolution}")

        # 参数校验
        if not all([device_name, app_package, app_activity]):
            logger.error("无法获取设备名称、应用包名或应用活动。")
            return

        # 启动界面分析
        # run_appium_inspector(device_name, app_package, app_activity, device_resolution)
        run_appium_inspector_by_lvm(device_name, app_package, app_activity, device_resolution)
    except Exception as e:
        logger.error(f"发生意外错误: {e}")


if __name__ == '__main__':
    main()
