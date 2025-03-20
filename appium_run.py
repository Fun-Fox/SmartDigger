"""
主入口模块

模块职责：
- 程序启动
- 日志配置
- 设备信息获取
- 主流程控制
"""

from source import AppiumInspector, capture_and_mark_elements, diagnose_and_handle
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
        page_source = driver.page_source
        recorder = Recorder()
        element_manager = ElementManager(recorder)
        # 生成 markdown
        recorder.generate_markdown()
        # 进行元素定位
        (screenshot_id, is_more_clickable_elements, grayscale_screenshot_path,
         marked_screenshot_path, single_color_screenshot_path) = capture_and_mark_elements(
            screenshot, device_name, app_package, page_source)
        # 进行弹窗识别
        if not is_more_clickable_elements:
            # 进行弹窗识别
            popup_id = diagnose_and_handle(grayscale_screenshot_path, marked_screenshot_path, )
            logger.info(f"弹窗标识为: {popup_id}")
            # 获取弹窗中心点
            if popup_id is not None and popup_id > 0:
                center_x, center_y = element_manager.element_center(single_color_screenshot_path,
                                                                    popup_id, screenshot_id)
                # 点击弹窗
                logger.info(f"检测到弹窗，弹窗标识为: {popup_id}，正在关闭...")
                click_element_close(driver, center_x, center_y)
            logger.info(f"弹窗关闭成功")
            driver.quit()
            recorder.close()
        logger.info(f"运行结束")
    except Exception as e:
        logger.error(f"运行 Appium Inspector 时发生错误: {e}")
        raise


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
        run_appium_inspector(device_name, app_package, app_activity, device_resolution)

    except Exception as e:
        logger.error(f"发生意外错误: {e}")


if __name__ == '__main__':
    main()
