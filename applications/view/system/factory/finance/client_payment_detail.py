# -*- coding: utf-8 -*-
# @Time    : 2024/7/8 20:36
# @File    : client_payment_detail.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-客户回款/工厂付款明细

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from applications.models import FactoryFinanceClientDetail
from applications.schemas import FactoryFinanceClientDetailSchema

bp = Blueprint('client_payment_detail', __name__, url_prefix='/factory/finance_statistics/client_payment/detail')


# 订单客户回款明细-主界面
@bp.get('/order_client/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:detail:main")
def main_order_client(finance_client_id):
    return render_template(
        'system/factory/finance_statistics/client_payment/detail/order_client/main.html',
        finance_client_id=finance_client_id
    )


# 订单客户回款明细-数据接口
@bp.get('/order_client/data_order_client/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:detail:main")
def data_order_client(finance_client_id):
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    data, count = get_finance_client_detail(finance_client_id)

    return table_api(data=data, count=count)


# 外发客户回款明细-主界面
@bp.get('/external_client/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:detail:main")
def main_external_client(finance_client_id):
    return render_template(
        'system/factory/finance_statistics/client_payment/detail/external_client/main.html',
        finance_client_id=finance_client_id
    )


# 外发客户回款明细-数据接口
@bp.get('/external_client/data_external_client/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:detail:main")
def data_external_client(finance_client_id):
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    data, count = get_finance_client_detail(finance_client_id)

    return table_api(data=data, count=count)


# 协作客户回款明细-主界面
@bp.get('/partner_client/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:detail:main")
def main_partner_client(finance_client_id):
    return render_template(
        'system/factory/finance_statistics/client_payment/detail/partner_client/main.html',
        finance_client_id=finance_client_id
    )


# 协作客户回款明细-数据接口
@bp.get('/partner_client/data_partner_client/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:detail:main")
def data_partner_client(finance_client_id):
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    data, count = get_finance_client_detail(finance_client_id)

    return table_api(data=data, count=count)


def get_finance_client_detail(finance_client_id):
    """
    获取客户回款/工厂付款明细数据
    :param query: 查询对象
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: result(列表数据), query_finance_client_detail（total）
    """
    query = db.session.query(FactoryFinanceClientDetail).filter(
        FactoryFinanceClientDetail.finance_client_id == finance_client_id
    )

    start_date = str_escape(request.args.get('startDate', type=str))
    end_date = str_escape(request.args.get('endDate', type=str))

    if start_date and not end_date:
        query = query.filter(FactoryFinanceClientDetail.date >= start_date)
    elif end_date and not start_date:
        query = query.filter(FactoryFinanceClientDetail.date <= end_date)
    elif start_date and end_date:
        query = query.filter(FactoryFinanceClientDetail.date >= start_date, FactoryFinanceClientDetail.date <= end_date)

    query_finance_client_detail = query.order_by(
        FactoryFinanceClientDetail.date.desc()
    ).layui_paginate()

    schema = FactoryFinanceClientDetailSchema(many=True)
    result = schema.dump(query_finance_client_detail)
    db.session.close()
    return result, query_finance_client_detail.total
