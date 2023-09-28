# ！/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time     : 2023/9/28
# @Author   : fanke.chang
# @File     : logging_config.py
# @Desc     :


import logging
import os.path
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))

# 配置日志
logging.basicConfig(
    filename=os.path.join(__dir__, 'shopify_script.log'),  # 日志文件名
    filemode='a',
    level=logging.INFO,       # 设置日志级别，可以选择DEBUG、INFO、WARNING、ERROR、CRITICAL等级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志消息格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 日期时间格式
)

# 获取一个名为 'example_logger' 的日志记录器
logger = logging.getLogger('shopify_producting')