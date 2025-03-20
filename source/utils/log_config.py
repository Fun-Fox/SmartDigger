import os
import logging
from logging.handlers import TimedRotatingFileHandler
import uuid

from flask import g


class TraceIdFilter(logging.Filter):
    """
    自定义日志过滤器，用于添加 trace_id
    """

    def filter(self, record):
        if not hasattr(record, 'trace_id'):
            try:
                record.trace_id = g.trace_id
            except Exception:
                record.trace_id = str(uuid.uuid4())
        return True


def setup_logger(name, log_dir="logs", log_file="app.log", level=logging.INFO, enable_console=True):
    """
    配置日志记录器
    :param name: 日志记录器名称
    :param log_dir: 日志文件保存目录
    :param log_file: 日志文件名
    :param level: 日志级别
    :param enable_console: 是否启用终端输出日志
    :return: 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_file)

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 防止日志传播到父记录器
    logger.propagate = False

    # 配置日志格式，添加 trace_id
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(trace_id)s - %(message)s')

    # 创建 TimedRotatingFileHandler，按天轮转日志文件
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight",
        interval=1,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # 添加 trace_id 过滤器
    trace_id_filter = TraceIdFilter()
    file_handler.addFilter(trace_id_filter)

    # 将处理器添加到日志记录器
    logger.addHandler(file_handler)

    # 如果启用终端输出，添加 StreamHandler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
