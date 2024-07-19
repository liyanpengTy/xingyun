# -*- coding: utf-8 -*-
# @Time    : 2024/7/7 0:08
# @File    : staff_wage_detail.py
# @Software: PyCharm
# @Author  : Roc

import calendar
from flask import Blueprint, render_template
from applications.common.utils.rights import authorize
from flask_login import current_user
from applications.common.utils.http import table_api, fail_api
from applications.extensions import db
from applications.models.factory.finance import FactoryFinanceStaff
from applications.models.factory.order import FactoryOrder
from applications.models.factory.cutting_bed import FactoryCuttingBed, FactoryCuttingBedDetails
from applications.models import FactoryStaff, Role
from applications.schemas.factory.cutting_bed import FactoryCuttingBedDetailsSchema

bp = Blueprint('staff_wage_detail', __name__, url_prefix='/factory/finance_statistics/staff_wage/detail')


# 财务统计-员工工资明细（按计件工资、页面数据）
@bp.get('/piecework/<int:finance_staff_id>')
@authorize('system:finance_statistics:staff_wage:detail:main')
def main_piecework(finance_staff_id):
    finance_staff = db.session.query(FactoryFinanceStaff).get(finance_staff_id)
    staff = db.session.query(FactoryStaff).get(finance_staff.staff_id)
    role = db.session.query(Role).get(finance_staff.role_id)
    enable = staff.enable
    if enable == 1:
        enable = "在职"
    elif enable == 0:
        enable = "离职"
    salary_type = staff.salary_type
    if salary_type == "fixed":
        salary_type = "固定工资"
    elif salary_type == "base_plus_commission":
        salary_type = "底薪+提成"
    elif salary_type == "piecework":
        salary_type = "计件工资"

    return render_template(
        'system/factory/finance_statistics/staff_wage/detail/piecework/main.html',
        finance_staff_id=finance_staff_id,
        finance_staff=finance_staff,
        staff=staff,
        role=role,
        enable=enable,
        salary_type=salary_type
    )


# 财务统计-员工工资明细（按计件工资、数据接口）
@bp.get('/piecework/data_piecework/<int:finance_staff_id>')
@authorize('system:finance_statistics:staff_wage:detail:main')
def data_piecework(finance_staff_id):
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    finance_staffs = db.session.query(FactoryFinanceStaff).get(finance_staff_id)
    if not finance_staffs:
        return fail_api(msg="工资信息不存在")

    dept_id = finance_staffs.dept_id
    staff_id = finance_staffs.staff_id
    # role_id = finance_staffs.role_id
    year = finance_staffs.year
    month = finance_staffs.month
    start_date = str(year) + "-" + str(month) + "-01" + " 00:00:00"
    end_date = str(year) + "-" + str(month) + "-" + str(calendar.monthrange(year, month)[1]) + " 23:59:59"
    orders = db.session.query(FactoryOrder).filter(
        FactoryOrder.dept_id == dept_id,
        # 增加order_status的筛选条件，只显示Packing和Completed状态的订单
        FactoryOrder.order_status.in_(['Packing', 'Completed']),
        FactoryOrder.is_deleted == 0
    ).all()
    cutting_beds = db.session.query(FactoryCuttingBed).filter(
        FactoryCuttingBed.order_id.in_([order.id for order in orders]),
        FactoryCuttingBed.is_bed == 0
    ).all()
    cutting_bed_details = db.session.query(FactoryCuttingBedDetails).filter(
        FactoryCuttingBedDetails.cutting_bed_id.in_([cutting_bed.id for cutting_bed in cutting_beds]),
        FactoryCuttingBedDetails.is_calculated == 1,
        FactoryCuttingBedDetails.staff_id == staff_id,
        FactoryCuttingBedDetails.delivery_date >= start_date,
        FactoryCuttingBedDetails.delivery_date <= end_date
    ).layui_paginate()

    schema = FactoryCuttingBedDetailsSchema(many=True)
    result = schema.dump(cutting_bed_details)
    # 计算每一条数据的总价格
    for item in result:
        item['total_price'] = int(item['staff_shipment_number']) * float(item['staff_unit_price'])

    return table_api(data=result, count=cutting_bed_details.total)


# 财务统计-员工工资明细（按底薪+提成、页面数据）
@bp.get('/base_plus_commission/<int:finance_staff_id>')
@authorize('system:finance_statistics:staff_wage:detail:main')
def main_base_plus_commission(finance_staff_id):
    finance_staff = db.session.query(FactoryFinanceStaff).get(finance_staff_id)
    staff = db.session.query(FactoryStaff).get(finance_staff.staff_id)
    role = db.session.query(Role).get(finance_staff.role_id)
    enable = staff.enable
    if enable == 1:
        enable = "在职"
    elif enable == 0:
        enable = "离职"
    salary_type = staff.salary_type
    if salary_type == "fixed":
        salary_type = "固定工资"
    elif salary_type == "base_plus_commission":
        salary_type = "底薪+提成"
    elif salary_type == "piecework":
        salary_type = "计件工资"

    return render_template(
        'system/factory/finance_statistics/staff_wage/detail/base_plus_commission/main.html',
        finance_staff_id=finance_staff_id,
        finance_staff=finance_staff,
        staff=staff,
        role=role,
        enable=enable,
        salary_type=salary_type
    )


# 财务统计-员工工资明细（按底薪+提成、数据接口）
@bp.get('/base_plus_commission/data_base_plus_commission/<int:finance_staff_id>')
@authorize('system:finance_statistics:staff_wage:detail:main')
def data_base_plus_commission(finance_staff_id):
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    finance_staffs = db.session.query(FactoryFinanceStaff).get(finance_staff_id)
    if not finance_staffs:
        return fail_api(msg="工资信息不存在")

    dept_id = finance_staffs.dept_id
    staff_id = finance_staffs.staff_id
    # role_id = finance_staffs.role_id
    year = finance_staffs.year
    month = finance_staffs.month
    start_date = str(year) + "-" + str(month) + "-01" + " 00:00:00"
    end_date = str(year) + "-" + str(month) + "-" + str(calendar.monthrange(year, month)[1]) + " 23:59:59"
    orders = db.session.query(FactoryOrder).filter(
        FactoryOrder.dept_id == dept_id,
        FactoryOrder.is_deleted == 0
    ).limit(1).first()
    sew_unit_price = orders.sew_unit_price

    finance_performances = db.session.query(FactoryFinancePerformance).filter(
        FactoryFinancePerformance.staff_id == staff_id,
        FactoryFinancePerformance.dept_id == dept_id,
        FactoryFinancePerformance.date >= start_date,
        FactoryFinancePerformance.date <= end_date
    ).layui_paginate()

    schema = FactoryFinancePerformanceSchema(many=True)
    result = schema.dump(finance_performances)
    # 计算每一条数据的总价格
    for item in result:
        item['total_price'] = int(item['piece_work_count']) * sew_unit_price
        item['sew_unit_price'] = sew_unit_price

    return table_api(data=result, count=finance_performances.total)