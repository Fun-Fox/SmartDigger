import time
import threading
from source.api import app
import schedule
from dotenv import load_dotenv

from source.job import cleanup_old_screenshots
from source.utils.log_config import setup_logger

# 配置日志
logger = setup_logger(__name__)

# 设置定时任务，每天凌晨1点执行
schedule.every().day.at("01:00").do(cleanup_old_screenshots)

# 启动定时任务
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)
        logger.info("定时任务启动成功")

load_dotenv()

if __name__ == '__main__':
    # 启动接口
    app.run(host='0.0.0.0', port=5000, debug=True)
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()