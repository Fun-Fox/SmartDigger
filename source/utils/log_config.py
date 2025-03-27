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
                from flask import g
                record.trace_id = g.trace_id
            except (RuntimeError, AttributeError):
                # 如果没有 Flask 上下文，使用默认的 trace_id
                record.trace_id = "子线程：" + str(uuid.uuid4())
        return True


def _create_file_handler(log_file_path, log_format):
    """
    创建文件日志处理器
    """
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight",
        interval=1,
        backupCount=3,
        encoding="utf-8",
        delay=True
    )
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(TraceIdFilter())
    return file_handler


def _create_console_handler(log_format):
    """
    创建终端日志处理器
    """
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    return console_handler


def setup_logger(name, log_dir="logs", log_file="app.log", level=logging.INFO, enable_console=True, log_format=None):
    """
    配置日志记录器
    :param name: 日志记录器名称
    :param log_dir: 日志文件保存目录
    :param log_file: 日志文件名
    :param level: 日志级别
    :param enable_console: 是否启用终端输出日志
    :param log_format: 自定义日志格式
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

    # 如果日志记录器已配置，直接返回
    if logger.handlers:
        return logger

    # 配置日志格式，添加行号字段
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(trace_id)s - %(lineno)d - %(message)s'

    # 添加文件处理器
    file_handler = _create_file_handler(log_file_path, log_format)
    logger.addHandler(file_handler)

    # 如果启用终端输出，添加终端处理器
    if enable_console:
        console_handler = _create_console_handler(log_format)
        logger.addHandler(console_handler)

    return logger
