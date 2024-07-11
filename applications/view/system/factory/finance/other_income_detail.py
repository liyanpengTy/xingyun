# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 20:00
# @File    : other_income_detail.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-收支统计-其他收入明细

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from applications.models import IncomeExpenditureStatistics
from applications.schemas import IncomeExpenitureStatisticsSchema

bp = Blueprint('other_income_detail', __name__, url_prefix='/factory/finance_statistics/statistics/detail/other_income')


# 财务统计-收支统计-其他收入明细-主界面
@bp.get('/')
@authorize("system:finance_statistics:client_payment:detail:main")
def main():
    return render_template(
        'system/factory/finance_statistics/statistics/detail/main.html'
    )


# 财务统计-收支统计-其他收入明细-数据接口
@bp.get('/data')
@authorize("system:finance_statistics:client_payment:detail:main")
def data():
    pass