# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 19:55
# @File    : statistics.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-收支统计

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from applications.models import IncomeExpenditureStatistics, FactoryFinanceStaff, FactoryClient, FactoryFinanceClient, FactoryFinanceOther, OtherIncomeDetail
from applications.schemas import IncomeExpenitureStatisticsSchema
from applications.common.utils.get_date import get_date

bp = Blueprint('statistics', __name__, url_prefix='/factory/finance_statistics/statistics')


# 财务统计-收支统计-主界面
@bp.get('/')
@authorize("system:finance_statistics:statistics:main")
def main():
    return render_template(
        'system/factory/finance_statistics/statistics/main.html'
    )


# 财务统计-收支统计-数据接口
@bp.get('/data')
@authorize("system:finance_statistics:statistics:main")
def data():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    year_month = request.args.get('yearMonth', type=str)

    query = db.session.query(IncomeExpenditureStatistics).filter(
        IncomeExpenditureStatistics.dept_id == current_user.dept_id
    )

    if year_month:
        year = year_month[:4]
        month = year_month[5:]
        query = query.filter(
            IncomeExpenditureStatistics.year == year,
            IncomeExpenditureStatistics.month == month
        )

    query_income_expenditure_statistics = query.order_by(
        IncomeExpenditureStatistics.year.desc(),
        IncomeExpenditureStatistics.month.desc()
    ).layui_paginate()

    schema = IncomeExpenitureStatisticsSchema(many=True)
    result = schema.dump(query_income_expenditure_statistics)

    for item in result:
        income = item['client_payment_factory'] + item['other_income']
        expenditure = item['employee_wage_expenses'] + item['factory_payment_client'] + item['other_expenses']
        item['cash_surplus'] = income - expenditure

    db.session.close()
    return table_api(data=result, count=query_income_expenditure_statistics.total)


# 财务统计-收支统计-生成数据（保存）
@bp.post('/create_save')
@authorize("system:finance_statistics:statistics:create")
def create_save():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    year, month, start_date, end_date = get_date()

    dept_id = current_user.dept_id

    try:
        """ 获取员工工资收支统计数据 """
        finance_staff_db = db.session.query(FactoryFinanceStaff).filter(
            FactoryFinanceStaff.dept_id == dept_id,
            FactoryFinanceStaff.year == year,
            FactoryFinanceStaff.month == month
        ).all()

        """ 获取本工厂的所有订单客户的收支统计数据 """
        client_type = ['orderClient']
        client_order_db = get_client(client_type)
        finance_order_client_db = db.session.query(FactoryFinanceClient).filter(
            FactoryFinanceClient.dept_id == dept_id,
            FactoryFinanceClient.client_id.in_([order_client.id for order_client in client_order_db]),
            FactoryFinanceClient.year == year,
            FactoryFinanceClient.month == month
        ).all()

        """ 获取本工厂的“外发客户”,“协作客户”的收支统计数据 """
        client_type = ['externalClient', 'partnerClient']
        client_other_db = get_client(client_type)
        finance_other_client_db = db.session.query(FactoryFinanceClient).filter(
            FactoryFinanceClient.dept_id == dept_id,
            FactoryFinanceClient.client_id.in_([other_client.id for other_client in client_other_db]),
            FactoryFinanceClient.year == year,
            FactoryFinanceClient.month == month
        )

        """ 获取其它开销的收支统计数据 """
        finance_other_db = db.session.query(FactoryFinanceOther).filter(
            FactoryFinanceOther.dept_id == dept_id,
            FactoryFinanceOther.year == year,
            FactoryFinanceOther.month == month
        ).all()

        income_expenditure_statistics = db.session.query(IncomeExpenditureStatistics).filter_by(
            dept_id=dept_id,
            year=year,
            month=month
        ).first()

        if income_expenditure_statistics:
            db.session.query(IncomeExpenditureStatistics).filter_by(id=income_expenditure_statistics.id).update(
                {
                    'client_payment_factory': sum([order_client.received for order_client in finance_order_client_db]),
                    'employee_wage_expenses': sum([staff.salary for staff in finance_staff_db]),
                    'other_expenses': sum([other.total_amount for other in finance_other_db]),
                    'factory_payment_client': sum([other_client.paid for other_client in finance_other_client_db])
                }
            )
            db.session.commit()
            return success_api(msg='收支统计数据更新成功')
        else:
            db.session.add(
                IncomeExpenditureStatistics(
                    dept_id=dept_id,
                    year=year,
                    month=month,
                    client_payment_factory=sum([order_client.received for order_client in finance_order_client_db]),
                    employee_wage_expenses=sum([staff.salary for staff in finance_staff_db]),
                    other_expenses=sum([other.total_amount for other in finance_other_db]),
                    factory_payment_client=sum([other_client.paid for other_client in finance_other_client_db])
                )
            )
            db.session.commit()
            return success_api(msg='收支统计数据新增成功')

    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='收支统计数据生成失败')
    finally:
        db.session.close()


def get_client(client_type):
    """
    获取本工厂的“订单客户”,“外发客户”,“协作客户”的客户信息
    :param client_type: 客户类型列表
    :return: 客户信息列表
    """
    client_db = client_order_db = db.session.query(FactoryClient).filter(
        FactoryClient.dept_id == current_user.dept_id,
        FactoryClient.client_type.in_(client_type),
        FactoryClient.is_deleted == 0
    ).all()
    return client_db



# 财务统计-收支统计-新增其它收入-弹框数据
@bp.get('/add')
@authorize("system:finance_statistics:statistics:add")
def add():
    return render_template(
        'system/factory/finance_statistics/statistics/add.html'
    )


# 财务统计-收支统计-新增其它收入-保存数据
@bp.post('/add_save')
@authorize("system:finance_statistics:statistics:add")
def add_save():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    req = request.get_json(force=True)
    date = req.get('date')
    category = req.get('category')
    unit_price = req.get('unitPrice')
    quantity = req.get('quantity')
    unit = req.get('unit')

    if not date:
        return fail_api(msg='日期不能为空')
    if not category:
        return fail_api(msg='类别/名称不能为空')
    if not unit_price:
        return fail_api(msg='单价不能为空')
    else:
        if float(unit_price) <= 0:
            return fail_api(msg='单价必须为正数')
    if not quantity:
        return fail_api(msg='数量不能为空')

    year = date[:4]
    month = date[5:7]

    dept_id = current_user.dept_id

    amount = float(unit_price) * float(quantity)

    try:
        income_expenditure_statistics = db.session.query(IncomeExpenditureStatistics).filter_by(
            dept_id=dept_id,
            year=year,
            month=month
        ).first()
        if not income_expenditure_statistics:
            return fail_api(msg='选择的日期【{}】不存在收支统计数据'.format(date))


        other_income_detail = OtherIncomeDetail(
            income_id=income_expenditure_statistics.id,
            date=date,
            category=category,
            unit_price=unit_price,
            quantity=quantity,
            unit=unit,
            amount=amount
        )
        db.session.add(other_income_detail)
        other_income = float(income_expenditure_statistics.other_income) + amount
        db.session.query(IncomeExpenditureStatistics).filter_by(id=income_expenditure_statistics.id).update(
            {
                'other_income': other_income
            }
        )
        db.session.commit()
        return success_api(msg='新增其它收入成功')

    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='新增其它收入失败')
    finally:
        db.session.close()
