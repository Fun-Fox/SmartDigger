"""
元素管理模块

模块职责：
- 管理应用界面元素
- 处理元素点击操作
"""

from source.services.recorder import Recorder

class ElementManager:
    """管理应用界面元素的类"""

    def __init__(self, recorder: Recorder, driver):
        """初始化 ElementManager
        
        参数:
            recorder: 数据记录器实例
            driver: Appium 驱动实例
        """
        self.recorder = recorder
        self.driver = driver

    def click_element_center(self, element_id, screenshot_id):
        """点击指定元素的中心点
        
        参数:
            element_id: 元素ID
            screenshot_id: 截图ID
            
        异常:
            ValueError: 当未找到指定元素时抛出
        """
        print(f"点击元素 ID: {element_id}, 截图 ID: {screenshot_id}")
        
        # 从数据库获取元素坐标
        self.recorder.cursor.execute('SELECT x1, y1, x2, y2 FROM elements WHERE element_id = ? and screenshot_id = ?',
                                     (element_id, screenshot_id,))
        result = self.recorder.cursor.fetchone()
        
        if result:
            x1, y1, x2, y2 = result
            # 计算中心点坐标
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            # 执行点击操作
            self.driver.tap([(center_x, center_y)])
        else:
            raise ValueError(f"未找到 ID 为 {element_id} 的元素")