# -*- coding: utf-8 -*-
# @Time    : 2024/7/8 20:04
# @File    : other_expenses_detail.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-其他支出-明细

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.models import FactoryFinanceOther, FactoryFinanceOtherDetail
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from applications.schemas import FactoryFinanceOtherDetailSchema

bp = Blueprint('other_expenses_detail', __name__, url_prefix='/factory/finance_statistics/other_expenses/detail')


# 财务统计-其他支出-明细
@bp.get('/<int:other_id>')
@authorize("system:finance_statistics:other_expenses:detail:main")
def main(other_id):
    return render_template('system/factory/finance_statistics/other_expenses/detail/main.html', other_id=other_id)


# 财务统计-其他支出-明细-数据
@bp.get('/data/<int:other_id>')
@authorize("system:finance_statistics:other_expenses:detail:main")
def data(other_id):
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    year_month = request.args.get('yearMonth', type=str)

    query = db.session.query(FactoryFinanceOtherDetail).filter(
        FactoryFinanceOtherDetail.other_id == other_id,
    )
    if year_month:
        query = query.filter(FactoryFinanceOtherDetail.date == year_month)

    query_finance_other_detail = query.order_by(
        FactoryFinanceOtherDetail.date
    ).layui_paginate()

    schema = FactoryFinanceOtherDetailSchema(many=True)
    result = schema.dump(query_finance_other_detail)
    db.session.close()
    return table_api(data=result, count=query_finance_other_detail.total)


# 财务统计-其他支出-明细-修改（弹框数据）
@bp.get('/edit/<int:detail_id>')
@authorize("system:finance_statistics:other_expenses:detail:edit")
def edit(detail_id):
    other_detail = db.session.query(FactoryFinanceOtherDetail).get(detail_id)
    return render_template('system/factory/finance_statistics/other_expenses/detail/edit.html', other_detail=other_detail)


# 财务统计-其他支出-明细-修改（保存）
@bp.put('/update')
@authorize("system:finance_statistics:other_expenses:detail:edit")
def update():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req = request.get_json(force=True)
    detail_id = str_escape(req.get('id'))
    category = str_escape(req.get('category'))
    name = str_escape(req.get('name'))
    unit_price = str_escape(req.get('unitPrice'))
    quantity = str_escape(req.get('quantity'))
    unit = str_escape(req.get('unit'))

    detail_data = {}

    if not category:
        return fail_api(msg='请输入类别')
    detail_data['category'] = category
    if not name:
        return fail_api(msg='请输入名称')
    detail_data['name'] = name
    if not unit_price:
        return fail_api(msg='请输入单价')
    else:
        # 判断单价是否为正数,可以为小数
        if not unit_price.replace('.', '').isdigit() or float(unit_price) <= 0:
            return fail_api(msg='单价必须为正数')
    detail_data['unit_price'] = float(unit_price)
    if not quantity:
        return fail_api(msg='请输入数量')
    else:
        # 判断数量是否为正整数
        if not quantity.isdigit() or int(quantity) <= 0:
            return fail_api(msg='数量必须为正整数')
    detail_data['quantity'] = int(quantity)
    detail_data['unit'] = unit
    detail_data['amount'] = float(unit_price) * int(quantity)

    try:
        details = db.session.query(FactoryFinanceOtherDetail).filter(
            FactoryFinanceOtherDetail.id == detail_id
        ).first()
        if details.amount != detail_data['amount']:
            other = db.session.query(FactoryFinanceOther).filter_by(id=details.other_id).first()
            total_amount = float(other.total_amount) - float(details.amount) + detail_data['amount']
            # 金额发生变化，更新总金额
            db.session.query(FactoryFinanceOther).filter_by(id=details.other_id).update(
                {'total_amount': total_amount}
            )
        db.session.query(FactoryFinanceOtherDetail).filter_by(id=detail_id).update(detail_data)
        db.session.commit()
        return success_api(msg='更新成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='更新失败')
    finally:
        db.session.close()