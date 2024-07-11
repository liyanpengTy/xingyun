# -*- coding: utf-8 -*-
# @Time    : 2024/7/11 0:26
# @File    : statistics_detail.py
# @Software: PyCharm
# @Author  : Roc
from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from applications.models import OtherIncomeDetail, IncomeExpenditureStatistics
from applications.schemas import OtherIncomeDetailSchema

bp = Blueprint('statistics_detail', __name__, url_prefix='/factory/finance_statistics/statistics/detail')


# 财务统计-收支统计-其他收入详情-主页面
@bp.get('/main/<int:income_id>')
@authorize("system:finance_statistics:statistics:detail:main")
def main(income_id):
    return render_template(
        '/system/factory/finance_statistics/statistics/detail/main.html',
        income_id=income_id
    )



# 财务统计-收支统计-其他收入详情-数据接口
@bp.get('/data/<int:income_id>')
@authorize("system:finance_statistics:statistics:detail:main")
def data(income_id):
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    start_date = request.args.get('startDate', type=str)
    end_date = request.args.get('endDate', type=str)

    query = db.session.query(OtherIncomeDetail).filter(
        OtherIncomeDetail.income_id == income_id,
        OtherIncomeDetail.is_delete == 0
    )

    if start_date and not end_date:
        query = query.filter(OtherIncomeDetail.date >= start_date)
    elif end_date and not start_date:
        query = query.filter(OtherIncomeDetail.date <= end_date)
    elif start_date and end_date:
        query = query.filter(OtherIncomeDetail.date >= start_date, OtherIncomeDetail.date <= end_date)

    query_other_income_detail = query.order_by(
        OtherIncomeDetail.date
    ).layui_paginate()

    schema = OtherIncomeDetailSchema(many=True)
    result = schema.dump(query_other_income_detail)
    db.session.close()
    return table_api(data=result, count=query_other_income_detail.total)


# 财务统计-收支统计-其他收入详情-修改（弹框数据）
@bp.get('/edit/<int:other_income_detail_id>')
@authorize("system:finance_statistics:statistics:detail:edit")
def edit(other_income_detail_id):
    other_income_detail = db.session.query(OtherIncomeDetail).get(other_income_detail_id)

    return render_template(
        '/system/factory/finance_statistics/statistics/detail/edit.html',
        other_income_detail=other_income_detail
    )


# 财务统计-收支统计-其他收入详情-修改（保存数据）
@bp.put('/update')
@authorize("system:finance_statistics:statistics:detail:edit")
def update():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req = request.get_json(force=True)
    other_income_detail_id = req.get('id')
    income_id = req.get('incomeId')
    category = req.get('category')
    unit_price = req.get('unitPrice')
    quantity = req.get('quantity')
    unit = req.get('unit')

    if not category:
        return fail_api(msg='类别/名称不能为空')
    if not unit_price:
        return fail_api(msg='单价不能为空')
    else:
        if float(unit_price) <= 0:
            return fail_api(msg='单价必须为正数')
    if not quantity:
        return fail_api(msg='数量不能为空')

    try:
        income_expenditure_statistics = db.session.query(IncomeExpenditureStatistics).filter_by(id=income_id).first()
        if not income_expenditure_statistics:
            return fail_api(msg='收支统计信息不存在')
        other_income_old = income_expenditure_statistics.other_income

        other_income_detail = db.session.query(OtherIncomeDetail).filter_by(id=other_income_detail_id, is_delete=0).first()
        if not other_income_detail:
            return fail_api(msg='这条收入信息不存在或已删除')
        amount_old = other_income_detail.amount

        db.session.query(OtherIncomeDetail).filter_by(id=other_income_detail_id).update({
            'category': category,
            'unit_price': unit_price,
            'quantity': quantity,
            'unit': unit,
            'amount': float(unit_price) * float(quantity)
        })
        other_income_new = float(other_income_old) - float(amount_old) + (float(unit_price) * float(quantity))

        db.session.query(IncomeExpenditureStatistics).filter_by(id=income_id).update({
            'other_income': other_income_new
        })
        db.session.commit()
        return success_api(msg='其它收入信息修改成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='其它收入信息修改失败')
    finally:
        db.session.close()


# 财务统计-收支统计-其他收入详情-删除
@bp.delete('/remove/<int:other_income_detail_id>')
@authorize("system:finance_statistics:statistics:detail:remove", log=True)
def delete(other_income_detail_id):
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    try:
        other_income_detail = db.session.query(OtherIncomeDetail).filter_by(id=other_income_detail_id, is_delete=0).first()
        if not other_income_detail:
            return fail_api(msg='这条收入信息不存在或已删除')
        amount_old = other_income_detail.amount

        income_expenditure_statistics = db.session.query(IncomeExpenditureStatistics).filter_by(id=other_income_detail.income_id).first()
        if not income_expenditure_statistics:
            return fail_api(msg='收支统计信息不存在')
        other_income_old = income_expenditure_statistics.other_income

        db.session.query(OtherIncomeDetail).filter_by(id=other_income_detail_id, is_delete=0).update({
            'is_delete': 1
        })

        other_income_new = float(other_income_old) - float(amount_old)
        db.session.query(IncomeExpenditureStatistics).filter_by(id=other_income_detail.income_id).update({
            'other_income': other_income_new
        })
        db.session.commit()
        return success_api(msg='删除成功')

    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='删除失败')
    finally:
        db.session.close()


