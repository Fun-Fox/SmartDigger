# 定义清理旧截图的任务
import os
import time

from dotenv import load_dotenv

from source.utils.log_config import setup_logger

logger = setup_logger(__name__)
# 获取当前脚本的绝对路径
current_file_path = os.path.abspath(__file__)
# 推导项目根目录（假设项目根目录是当前脚本的祖父目录）
project_root = os.path.dirname(os.path.dirname(current_file_path))
load_dotenv()


def clean_old_screenshots(directory_path, days=3, do=False):
    """清理超过指定天数的旧截图

    参数:
        directory_path: 截图保存路径
        days: 保留的天数，默认为3天
    """
    try:
        now = time.time()
        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.path.isfile(file_path):
                    # 获取文件的最后修改时间
                    file_mtime = os.path.getmtime(file_path)
                    # 如果文件超过指定天数，则删除
                    if do:
                        os.remove(file_path)
                        logger.info(f"删除旧截图: {file_path}")
                    elif do is False and now - file_mtime > days * 86400:  # 86400秒 = 1天
                        os.remove(file_path)
                        logger.info(f"删除旧截图: {file_path}")
    except Exception as e:
        logger.error(f"清理旧截图时发生错误: {str(e)}")


def cleanup_old_screenshots():
    tmp_dir = os.getenv('TMP_DIR')  # 截图保存路径
    clean_old_screenshots(os.path.join(project_root, tmp_dir))
    screenshot_dir = os.getenv('SCREENSHOT_DIR')  # 截图保存路径
    clean_old_screenshots(os.path.join(project_root, screenshot_dir))


if __name__ == '__main__':
    tmp_dir = os.getenv('TMP_DIR')  # 截图保存路径
    clean_old_screenshots(os.path.join(project_root, tmp_dir), do=True)
    screenshot_dir = os.getenv('SCREENSHOT_DIR')  # 截图保存路径
    clean_old_screenshots(os.path.join(project_root, screenshot_dir), do=True)
