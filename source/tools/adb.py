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
