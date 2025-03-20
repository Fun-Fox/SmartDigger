import cv2
import os
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
# 获取当前脚本的绝对路径
current_file_path = os.path.abspath(__file__)
# 推导项目根目录（假设项目根目录是当前脚本的祖父目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))

load_dotenv()


class TemplateMatcher:
    def __init__(self):
        self.template_dir = os.path.join(project_root, os.getenv('TEMPLATE_DIR'))
        print(self.template_dir)
        # 初始化日志记录器
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def match_known_popups(self, screenshot_path):
        """匹配已知弹窗模板"""
        screenshot = cv2.imread(screenshot_path, 0)
        if screenshot is None:
            logger.error(f"无法读取截图文件: {screenshot_path}")
            return {'found': False}

        for template_file in os.listdir(self.template_dir):
            template_path = os.path.join(self.template_dir, template_file)
            template = cv2.imread(template_path, 0)
            if template is None:
                logger.error(f"无法读取模板文件: {template_path}")
                continue

            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val > 0.8:  # 匹配阈值
                logger.info(f"匹配到弹窗模板: {template_file}, 匹配值: {max_val}, 位置: {max_loc}")
                return True, template_file
        logger.info("未匹配到任何弹窗模板")
        return False


if __name__ == '__main__':
    template_matcher = TemplateMatcher()
    result, template_file = template_matcher.match_known_popups(
        'D:\Code\SmartDigger\screenshots\HJS5T19718001742\HJS5T19718001742_20250319_181835_com.android.settings_single_color_screenshot.jpeg')
    print(result)
    print(template_file.rstrip('.png'))
