import subprocess
from dotenv import load_dotenv
from source.utils.log_config import setup_logger

logger = setup_logger(__name__)
load_dotenv()
__all__ = ['AdbHelper']


class AdbHelper:
    """ADB 操作工具类"""

    @staticmethod
    def tap_on_device(device_name, x, y):
        """
        在指定设备的屏幕上模拟点击指定坐标
        :param device_name: 设备名称（可通过 get_device_name 获取）
        :param x: 点击的 X 坐标
        :param y: 点击的 Y 坐标
        """
        try:
            # 使用 adb shell input tap 命令模拟点击
            subprocess.run(
                ['adb', '-s', device_name, 'shell', 'input', 'tap', str(x), str(y)],
                check=True
            )
            logger.info(f"在设备 {device_name} 上成功点击坐标 ({x}, {y})")
        except subprocess.CalledProcessError as e:
            logger.error(f"在设备 {device_name} 上点击坐标 ({x}, {y}) 失败: {str(e)}")
            raise

    @staticmethod
    def get_device_name():
        """获取设备名称"""
        try:
            result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, text=True)
            devices = [line.split()[0] for line in result.stdout.splitlines()[1:] if line.strip()]
            if not devices:
                raise Exception("No devices found. Please connect an Android device or start an emulator.")
            return devices[0]
        except Exception as e:
            logger.error(f"获取设备名称失败: {str(e)}")
            raise

    @staticmethod
    def get_device_resolution():
        """获取设备分辨率"""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'wm', 'size'],
                stdout=subprocess.PIPE, text=True
            )
            output = result.stdout.strip()
            if output:
                resolution = output.split()[-1]  # 例如 "1080x1920"
                width, height = map(int, resolution.split('x'))
                return width, height
            raise Exception("无法获取设备屏幕分辨率，请确保设备已连接并正常运行。")
        except Exception as e:
            logger.error(f"获取设备分辨率失败: {str(e)}")
            raise

    @staticmethod
    def get_current_app_activity():
        """获取当前应用活动"""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'dumpsys', 'window', 'displays', '|', 'grep', '-E', 'mCurrentFocus'],
                stdout=subprocess.PIPE, text=True
            )
            for line in result.stdout.splitlines():
                if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                    parts = line.split()
                    if len(parts) > 2:
                        return parts[-1].split('/')[1][:-1]
            raise Exception("无法获取当前应用活动")
        except Exception as e:
            logger.error(f"获取应用活动失败: {str(e)}")
            raise

    @staticmethod
    def get_current_app_package():
        """获取当前应用包名"""
        try:
            result = subprocess.run(
                ['adb', 'shell', 'dumpsys', 'window', 'displays', '|', 'grep', '-E', 'mCurrentFocus'],
                stdout=subprocess.PIPE, text=True
            )
            for line in result.stdout.splitlines():
                if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                    parts = line.split()
                    if len(parts) > 2:
                        return parts[-1].split('/')[0]
            raise Exception("无法获取当前应用的包名，请确保设备上有正在运行的应用。")
        except Exception as e:
            logger.error(f"获取应用包名失败: {str(e)}")
            raise

    @staticmethod
    def get_screenshot_base64(device_name):
        """
        获取设备屏幕截图并以 base64 格式返回
        :param device_name: 设备名称
        :return: 屏幕截图的 base64 字符串
        """
        try:
            # 使用 adb shell screencap 命令获取屏幕截图
            result = subprocess.run(
                ['adb', '-s', device_name, 'shell', 'screencap', '-p'],
                stdout=subprocess.PIPE, check=True
            )
            # 将截图数据转换为 base64 编码
            import base64
            screenshot_base64 = base64.b64encode(result.stdout).decode('utf-8')
            logger.info(f"成功获取设备 {device_name} 的屏幕截图")
            return screenshot_base64
        except subprocess.CalledProcessError as e:
            logger.error(f"获取设备 {device_name} 的屏幕截图失败: {str(e)}")
            raise

    @staticmethod
    def get_screen_xml(device_name):
        """
        获取设备当前屏幕的 XML 布局
        :param device_name: 设备名称
        :return: 屏幕的 XML 布局字符串
        """
        try:
            # 使用 adb shell uiautomator dump 命令获取屏幕 XML 布局
            subprocess.run(
                ['adb', '-s', device_name, 'shell', 'uiautomator', 'dump', '/sdcard/ui_tree.xml'],
                check=True
            )
            # 将 XML 文件从设备拉取到本地
            subprocess.run(
                ['adb', '-s', device_name, 'pull', '/sdcard/ui_tree.xml', './ui_tree.xml'],
                check=True
            )
            # 读取并返回 XML 内容
            with open('./ui_tree.xml', 'r', encoding='utf-8') as file:
                xml_content = file.read()
            logger.info(f"成功获取设备 {device_name} 的屏幕 XML 布局")
            return xml_content
        except subprocess.CalledProcessError as e:
            logger.error(f"获取设备 {device_name} 的屏幕 XML 布局失败: {str(e)}")
            raise


if __name__ == "__main__":
    # 测试 get_device_name() 函数
    device_name = AdbHelper.get_device_name()
    print(f"设备名称: {device_name}")

    # 测试 get_device_resolution() 函数
    width, height = AdbHelper.get_device_resolution()
    print(f"设备分辨率: {width}x{height}")

    # 测试 get_current_app_activity() 函数
    activity = AdbHelper.get_current_app_activity()
    print(f"当前应用活动: {activity}")

    screenshot_base64 = AdbHelper.get_screenshot_base64(device_name)
    print(f"屏幕截图的 base64: {screenshot_base64}")

    xml_content = AdbHelper.get_screen_xml(device_name)
    print(f"屏幕 XML 布局: {xml_content}")
