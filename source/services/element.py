"""
元素管理模块

模块职责：
- 管理应用界面元素
- 处理元素点击操作
"""
import os

from source.services.image_processor import ImageProcessor
from source.services.recorder import Recorder

__all__ = ["ElementManager", "click_element_close"]


class ElementManager:
    """管理应用界面元素的类"""

    def __init__(self, recorder: Recorder):
        """初始化 ElementManager
        
        参数:
            recorder: 数据记录器实例
            driver: Appium 驱动实例
        """
        self.recorder = recorder
        self.imageProcessor = ImageProcessor()

    def element_center(self,  element_id, screenshot_id):
        """点击指定元素的中心点
        
        参数:
            element_id: 元素ID
            screenshot_id: 截图ID
            
        异常:
            ValueError: 当未找到指定元素时抛出
        """
        # 从数据库获取元素坐标
        self.recorder.cursor.execute(
            'SELECT center_x, center_y FROM elements WHERE element_id = ? and screenshot_id = ?',
            (element_id, screenshot_id,))
        result = self.recorder.cursor.fetchone()
        if result:
            center_x, center_y = result
            # 执行点击操作
            return center_x, center_y
        else:
            raise ValueError(f"未找到 ID 为 {element_id} 的元素")


def click_element_close(driver, center_x, center_y):
    driver.tap([(center_x, center_y)])
