# encoding:utf-8

import inspect
import logging
import sys

SWITCH = True


def _get_logger():
    log = logging.getLogger('log')
    log.setLevel(logging.INFO)
    console_handle = logging.StreamHandler(sys.stdout)
    console_handle.setFormatter(logging.Formatter('[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s',
                                                  datefmt='%Y-%m-%d %H:%M:%S'))
    log.addHandler(console_handle)
    log.propagate=False
    return log


def close_log():
    global SWITCH
    SWITCH = False


def debug(arg, *args):
    # 获取调用者的栈帧信息
    caller_frame = inspect.stack()[1]
    # 获取调用者的文件名和行号
    caller_file = caller_frame.filename
    caller_line = caller_frame.lineno

    # 将调用者的信息添加到日志消息中
    arg = f"[{caller_file}:{caller_line}] {arg}"

    if SWITCH:
        if len(args) == 0:
            logger.debug(arg)
        else:
            logger.debug(arg.format(*args))


def info(arg, *args):
    # 获取调用者的栈帧信息
    caller_frame = inspect.stack()[1]
    # 获取调用者的文件名和行号
    caller_file = caller_frame.filename
    caller_line = caller_frame.lineno

    # 将调用者的信息添加到日志消息中
    arg = f"[{caller_file}:{caller_line}] {arg}"

    if SWITCH:
        if len(args) == 0:
            logger.info(arg)
        else:
            logger.info(arg.format(*args))


def warn(arg, *args):
    # 获取调用者的栈帧信息
    caller_frame = inspect.stack()[1]
    # 获取调用者的文件名和行号
    caller_file = caller_frame.filename
    caller_line = caller_frame.lineno

    # 将调用者的信息添加到日志消息中
    arg = f"[{caller_file}:{caller_line}] {arg}"

    if len(args) == 0:
        logger.warning(arg)
    else:
        logger.warning(arg.format(*args))


def error(arg, *args):
    # 获取调用者的栈帧信息
    caller_frame = inspect.stack()[1]
    # 获取调用者的文件名和行号
    caller_file = caller_frame.filename
    caller_line = caller_frame.lineno

    # 将调用者的信息添加到日志消息中
    arg = f"[{caller_file}:{caller_line}] {arg}"

    if len(args) == 0:
        logger.error(arg)
    else:
        logger.error(arg.format(*args))


def exception(arg, *args):
    # 获取调用者的栈帧信息
    caller_frame = inspect.stack()[1]
    # 获取调用者的文件名和行号
    caller_file = caller_frame.filename
    caller_line = caller_frame.lineno

    # 将调用者的信息添加到日志消息中
    arg = f"[{caller_file}:{caller_line}] {arg}"

    if len(args) == 0:
        logger.exception(arg)
    else:
        logger.exception(arg.format(*args))

# 日志句柄
logger = _get_logger()
