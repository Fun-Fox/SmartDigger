import cv2
import os

import numpy as np

from source.utils.log_config import setup_logger

logger = setup_logger(__name__)

from dotenv import load_dotenv

load_dotenv()
# 获取当前脚本的绝对路径
current_file_path = os.path.abspath(__file__)
# 推导项目根目录（假设项目根目录是当前脚本的祖父目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path))))


class TemplateMatcher:
    def __init__(self):
        self.template_dir = os.path.join(project_root, os.getenv('TEMPLATE_DIR'))
        # 初始化日志记录器

    def match_known_popups(self, non_clickable_area_image):
        """匹配已知弹窗模板"""

        # non_clickable_area_image.save( os.path.join(project_root, os.getenv('TEMPLATE_DIR'), 'non_clickable_area_image.png'))
        non_clickable_area_image = np.array(non_clickable_area_image)
        for template_file_item in os.listdir(self.template_dir):
            template_path = os.path.join(self.template_dir, template_file_item)
            template = cv2.imread(template_path, 0)
            if template is None:
                logger.error(f"无法读取模板文件: {template_path}")
                continue
            ret = cv2.matchTemplate(non_clickable_area_image, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(ret)
            if max_val > 0.8:  # 匹配阈值
                logger.info(f"匹配到弹窗模板: {template_file_item}, 匹配值: {max_val}")
                return True, template_file_item
        logger.info("未匹配到任何弹窗模板")
        return False, None


# if __name__ == '__main__':
#     template_matcher = TemplateMatcher()
#     result = template_matcher.match_known_popups('D:\Code\SmartDigger\source\\test\\test-2.png')
#     print(result)
    # print(template_file.rstrip('.png'))
