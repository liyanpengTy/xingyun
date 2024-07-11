# -*- coding: utf-8 -*-
# @Time    : 2024/7/8 20:03
# @File    : other_expenses.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-其他支出

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.models import FactoryFinanceOther, FactoryFinanceOtherDetail
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from applications.schemas import FactoryFinanceOtherSchema

bp = Blueprint('other_expenses', __name__, url_prefix='/factory/finance_statistics/other_expenses')


# 财务统计-其他支出-列表
@bp.get('/')
@authorize('system:finance_statistics:other_expenses:main')
def main():
    return render_template('system/factory/finance_statistics/other_expenses/main.html')


# 财务统计-其他支出-数据
@bp.get('/data')
@authorize('system:finance_statistics:other_expenses:main')
def data():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    year_month = request.args.get('yearMonth', type=str)

    query = db.session.query(FactoryFinanceOther).filter(
        FactoryFinanceOther.dept_id == current_user.dept_id
    )

    if year_month:
        year = year_month[:4]
        month = year_month[5:]
        query = query.filter(
            FactoryFinanceOther.year == year,
            FactoryFinanceOther.month == month
        )

    query_finance_other = query.order_by(
        FactoryFinanceOther.year.desc(),
        FactoryFinanceOther.month.desc()
    ).layui_paginate()

    schema = FactoryFinanceOtherSchema(many=True)
    result = schema.dump(query_finance_other)
    db.session.close()
    return table_api(data=result, count=query_finance_other.total)


# 财务统计-其他支出-新增（弹框数据）
@bp.get('/add')
@authorize('system:finance_statistics:other_expenses:add')
def add():
    return render_template('system/factory/finance_statistics/other_expenses/add.html')


# 财务统计-其他支出-新增（保存）
@bp.post('/save')
@authorize('system:finance_statistics:other_expenses:add')
def save():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    req = request.get_json(force=True)
    date = str_escape(req.get('date'))
    category = str_escape(req.get('category'))
    name = str_escape(req.get('name'))
    unit_price = str_escape(req.get('unitPrice'))
    quantity = str_escape(req.get('quantity'))
    unit = str_escape(req.get('unit'))

    if not date:
        return fail_api(msg='请选择日期')
    if not category:
        return fail_api(msg='请输入类别')
    if not name:
        return fail_api(msg='请输入名称')
    if not unit_price:
        return fail_api(msg='请输入单价')
    else:
        # 判断单价是否为正数
        if not unit_price.isdigit() or float(unit_price) <= 0:
            return fail_api(msg='单价必须为正数')
    if not quantity:
        return fail_api(msg='请输入数量')
    else:
        # 判断数量是否为正整数
        if not quantity.isdigit() or int(quantity) <= 0:
            return fail_api(msg='数量必须为正整数')

    try:
        other = db.session.query(FactoryFinanceOther).filter(
            FactoryFinanceOther.dept_id == current_user.dept_id,
            FactoryFinanceOther.year == date.split('-')[0],
            FactoryFinanceOther.month == date.split('-')[1]
        ).first()
        if other:
            # 更新
            db.session.query(FactoryFinanceOther).filter_by(id=other.id).update({
                "detail_count": other.detail_count + 1,
                "total_amount": float(other.total_amount) + float(unit_price) * float(quantity)
            })
        else:
            # 新增
            other_expenses = FactoryFinanceOther(
                dept_id=current_user.dept_id,
                year=date.split('-')[0],
                month=date.split('-')[1],
                detail_count=1,
                total_amount=float(unit_price) * float(quantity)
            )
            db.session.add(other_expenses)
        # 查询其他开销主表，获取ID,关联到子表
        others = db.session.query(FactoryFinanceOther).filter(
            FactoryFinanceOther.dept_id == current_user.dept_id,
            FactoryFinanceOther.year == date.split('-')[0],
            FactoryFinanceOther.month == date.split('-')[1]
        ).first()
        # 新增详细表数据
        detail = FactoryFinanceOtherDetail(
            other_id=others.id,
            date=date,
            name=name,
            category=category,
            unit_price=unit_price,
            quantity=quantity,
            unit=unit,
            amount=float(unit_price) * float(quantity)
        )
        db.session.add(detail)
        db.session.commit()
        return success_api(msg='新增其它开销，保存成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='新增其它开销，保存失败')
    finally:
        db.session.close()