"""
主入口模块

模块职责：
- 程序启动
- 日志配置
- 设备信息获取
- 主流程控制
"""

import logging
from source.utils.adb import get_device_name, get_current_app_package, get_current_app_activity, get_device_resolution
from source.app import AppiumInspector
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.error("无效的输入参数：device_name、app_package 或 app_activity 为空。")
        raise ValueError("device_name、app_package 和 app_activity 必须为非空字符串。")

    try:
        inspector = AppiumInspector(device_name, app_package, app_activity, device_resolution)
        is_more_clickable_elements, grayscale_screenshot_path, marked_screenshot_path = inspector.capture_and_mark_elements()
        if not is_more_clickable_elements:
            inspector.diagnose_and_handle(grayscale_screenshot_path, marked_screenshot_path)

    except Exception as e:
        logging.error(f"运行 Appium Inspector 时发生错误: {e}")
        raise

def main():
    """主函数，获取设备信息并运行 Appium Inspector"""
    try:
        # 获取设备信息
        device_name = get_device_name()
        app_package = get_current_app_package()
        print(f"当前应用包名：{app_package}")
        app_activity = get_current_app_activity()
        print(f"当前应用活动：{app_activity}")
        device_resolution = get_device_resolution()
        print(f"设备分辨率：{device_resolution}")

        # 参数校验
        if not all([device_name, app_package, app_activity]):
            logging.error("无法获取设备名称、应用包名或应用活动。")
            return

        # 启动界面分析
        run_appium_inspector(device_name, app_package, app_activity, device_resolution)

    except Exception as e:
        logging.error(f"发生意外错误: {e}")

if __name__ == '__main__':
    main()