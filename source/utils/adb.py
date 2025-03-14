import subprocess
from dotenv import load_dotenv

load_dotenv()

def get_device_name():
    result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, text=True)
    devices = [line.split()[0] for line in result.stdout.splitlines()[1:] if line.strip()]
    if not devices:
        raise Exception("No devices found. Please connect an Android device or start an emulator.")
    return devices[0]

def get_device_resolution():
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

def get_current_app_activity():
    result = subprocess.run(
        ['adb', 'shell', 'dumpsys', 'window', 'displays', '|', 'grep', '-E', 'mCurrentFocus'],
        stdout=subprocess.PIPE, text=True
    )
    for line in result.stdout.splitlines():
        if 'mCurrentFocus' in line or 'mFocusedApp' in line:
            parts = line.split()
            if len(parts) > 2:
                return parts[-1].split('/')[1][:-1]
    raise Exception()

def get_current_app_package():
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
