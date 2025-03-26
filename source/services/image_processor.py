import os
import time

from PIL import ImageDraw, ImageFont, Image  # 添加 ImageFont 导入
import re
import random
from source.services.recorder import Recorder
import shutil
from source.utils.log_config import setup_logger


class ImageProcessor:
    """处理图片的类，包括灰度转换、绘制边框等操作"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.recorder = Recorder()

    def convert_to_grayscale(self, image) -> Image.Image:
        """将图片转换为灰度图
        
        参数:
            image: PIL Image 对象
            
        返回:
            灰度图 PIL Image 对象
        """
        return image.convert('L')

    def draw_element_borders(self, marked_screenshot_image, clickable_elements_bounds_list, screenshot_id) -> tuple[
        Image.Image, Image.Image]:
        """在图片上绘制元素的边框，并将不可点击部分改为单一色调（无框）

        参数:
            image: PIL Image 对象
            clickable_elements_bounds_list: 可点击元素边界信息列表，每个元素为 (bounds, element_id)
            screenshot_id: 截图 ID
            directory_path: 保存路径

        返回:
            marked_screenshot_path: 绘制边框后的图像路径
            single_color_screenshot_path: 单一色调后的图像路径
        """
        draw = ImageDraw.Draw(marked_screenshot_image)

        # 创建单一色调的图像副本
        non_clickable_area_image = marked_screenshot_image.copy()
        single_color_draw = ImageDraw.Draw(non_clickable_area_image)
        single_color = (192, 192, 192)  # 灰色

        # 将不可点击部分改为单一色调
        width, height = marked_screenshot_image.size
        for x in range(width):
            for y in range(height):
                is_clickable = False
                for bounds, _ in clickable_elements_bounds_list:
                    matches = re.findall(r'\d+', bounds)
                    x1, y1, x2, y2 = map(int, matches)
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        is_clickable = True
                        break
                if not is_clickable:
                    single_color_draw.point((x, y), fill=single_color)

        # 绘制可点击部分的边框和文字
        for bounds, element_id in clickable_elements_bounds_list:
            # 将可点击元素的值存于数据库中
            if self.recorder.is_record_exist(bounds, screenshot_id):
                continue
            self.recorder.save_bound(bounds, screenshot_id, element_id + 1)

            matches = re.findall(r'\d+', bounds)
            x1, y1, x2, y2 = map(int, matches)
            color_groups = [
                ["red", "maroon", "coral"],  # 红色组
                ["green", "olive"],  # 绿色组
                ["blue", "navy"]  # 蓝色组
            ]
            # 根据 element_id 选择颜色组
            group_index = element_id % 3
            color_group = color_groups[group_index]
            # 在组内随机选择颜色
            color = random.sample(color_group, 1)[0]

            self.logger.info(f"绘制边框和文本，颜色：{color}")

            # 绘制边框
            draw.rectangle([x1 + 5, y1 + 5, x2 - 5, y2 - 5], outline=color, width=5)

            # 绘制文本
            font_path = "fonts/Roboto_SemiCondensed-Black.ttf"
            font = ImageFont.truetype(font_path, size=40)
            text = f"{element_id + 1}"
            text_x = x2 - font.getmask(text).size[0] - 30
            text_y = y1 + 10
            draw.text((text_x + 10, text_y), text, fill=color, font=font)

        return marked_screenshot_image, non_clickable_area_image
        # return marked_screenshot_path, single_color_screenshot_path

    # # 保存绘制边框后的图像
    # marked_screenshot_path = self.save_screenshot(
    #     image, directory_path, screenshot_id, 'marked_screenshot', format='JPEG')
    # # directory_path = os.path.join(os.getenv('SCREENSHOT_DIR'), device_name)
    # #
    # # if not os.path.exists(directory_path):
    # #     os.makedirs(directory_path)
    # # 保存单一色调后的图像
    # single_color_screenshot_path = self.save_screenshot(
    #     single_color_image, directory_path, screenshot_id, 'single_color_screenshot', format='JPEG')

    # template_dir = os.path.join(os.getenv('TEMPLATE_DIR'), )
    # if not os.path.exists(template_dir):
    #     os.makedirs(template_dir)

    ## 存储于弹窗模版库(图形)
    # self.imageProcessor.copy_image(single_color_screenshot_path,
    #                                os.path.join(template_dir, f"{screenshot_id}.jpeg"))
    # self.recorder.save_template(screenshot_id, center_x, center_y)




if __name__ == '__main__':
    color_groups = [
        ["red", "maroon", "coral"],  # 红色组
        ["green", "olive"],  # 绿色组
        ["blue", "navy"]  # 蓝色组
    ]
    # 根据 element_id 选择颜色组
    group_index = 3 % 3
    color_group = color_groups[group_index]
    # 在组内随机选择颜色
    color = random.sample(color_group, 1)[0]
    print(color)
