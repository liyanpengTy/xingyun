# -*- coding: utf-8 -*-
# @Time    : 2024/7/10 20:04
# @File    : get_date.py
# @Software: PyCharm
# @Author  : Roc
import datetime

def get_date():
    """
    获取上个月的开始日期和结束日期
    :param year: 年份
    :param month: 月份
    :return: 开始日期和结束日期
    """
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1
    start_date = datetime.datetime(year, month, 1)
    end_date = datetime.datetime(year if month != 12 else year + 1, month + 1 if month != 12 else 1, 1)
    return year, month, start_date, end_date