#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强日志系统
Enhanced Logging System

提供统一的日志管理,支持文件轮转和性能监控
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from functools import wraps
import time
from typing import Callable


# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }

    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logger(
    name: str = 'russ_trading',
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    设置日志器

    Args:
        name: 日志器名称
        level: 日志级别
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台

    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已有的处理器
    logger.handlers.clear()

    # 日志格式
    detailed_fmt = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
    )
    simple_fmt = '%(asctime)s - %(levelname)s - %(message)s'

    # 文件处理器 - 按日期轮转
    if log_to_file:
        # 详细日志 (所有级别)
        file_handler = TimedRotatingFileHandler(
            filename=LOG_DIR / f'{name}.log',
            when='midnight',      # 每天午夜轮转
            interval=1,
            backupCount=30,       # 保留30天
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(detailed_fmt)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 错误日志 (单独文件)
        error_handler = RotatingFileHandler(
            filename=LOG_DIR / f'{name}_error.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(detailed_fmt)
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)

    # 控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = ColoredFormatter(simple_fmt)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def log_performance(logger: logging.Logger = None):
    """
    性能监控装饰器

    Args:
        logger: 日志器,如果未提供则使用默认日志器

    Usage:
        @log_performance()
        def slow_function():
            time.sleep(2)
    """
    if logger is None:
        logger = logging.getLogger('russ_trading')

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            try:
                logger.debug(f"[开始执行] {func_name}")
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # 性能分级
                if elapsed < 1.0:
                    logger.debug(f"[执行完成] {func_name} - 耗时: {elapsed:.3f}秒 ✅")
                elif elapsed < 5.0:
                    logger.info(f"[执行完成] {func_name} - 耗时: {elapsed:.3f}秒")
                else:
                    logger.warning(
                        f"[执行缓慢] {func_name} - 耗时: {elapsed:.3f}秒 "
                        f"⚠️ 建议优化"
                    )

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"[执行失败] {func_name} - "
                    f"耗时: {elapsed:.3f}秒 - 错误: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


def log_exception(logger: logging.Logger = None):
    """
    异常日志装饰器

    Args:
        logger: 日志器

    Usage:
        @log_exception()
        def may_fail():
            raise ValueError("Something went wrong")
    """
    if logger is None:
        logger = logging.getLogger('russ_trading')

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"函数 {func.__name__} 发生异常: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


# 全局默认日志器
default_logger = setup_logger()


if __name__ == '__main__':
    # 测试日志系统
    logger = setup_logger('test_logger', level=logging.DEBUG)

    logger.debug("这是DEBUG信息")
    logger.info("这是INFO信息")
    logger.warning("这是WARNING信息")
    logger.error("这是ERROR信息")

    print("\n=== 测试性能监控装饰器 ===")

    @log_performance(logger)
    def fast_function():
        time.sleep(0.5)
        return "快速完成"

    @log_performance(logger)
    def slow_function():
        time.sleep(6)
        return "缓慢完成"

    fast_function()
    # slow_function()  # 注释掉避免等待太久

    print("\n=== 测试异常日志装饰器 ===")

    @log_exception(logger)
    def error_function():
        raise ValueError("故意触发的错误")

    try:
        error_function()
    except ValueError:
        print("异常已被捕获并记录")

    print(f"\n日志文件保存在: {LOG_DIR}")
