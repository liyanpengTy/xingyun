# -*- coding: utf-8 -*-
# @Time    : 2024/7/6 16:31
# @File    : staff_wage.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-员工工资统计

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.common.utils.http import table_api, success_api, fail_api
from applications.models.factory.staff import FactoryStaff
from applications.models.factory.cutting_bed import FactoryCuttingBedDetails, FactoryCuttingBed
from applications.models.factory.order import FactoryOrder
from applications.models.factory.finance import FactoryFinanceStaff, FactoryFinanceSubsidy, FactoryFinancePerformance
from applications.models import Role
from applications.schemas.factory.finance import FactoryFinanceStaffSchema
from applications.extensions import db
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from applications.common.utils.get_date import get_date
import datetime

bp = Blueprint('staff_wage', __name__, url_prefix='/factory/finance_statistics/staff_wage')


# 财务统计-员工工资统计（主页）
@bp.get('/')
@authorize("system:finance_statistics:staff_wage:main")
def main():
    """ 工资管理 """
    staffs = db.session.query(FactoryStaff).filter(
        FactoryStaff.dept_id == current_user.dept_id,
        FactoryStaff.is_deleted == 0
    ).all()

    role_isd = []
    for staff in staffs:
        if staff.role_id not in role_isd:
            role_isd.append(staff.role_id)
    roles = db.session.query(Role).filter(Role.id.in_(role_isd)).all()

    return render_template('system/factory/finance_statistics/staff_wage/main.html', staffs=staffs, roles=roles)


# 财务统计-员工工资统计（列表数据）
@bp.get('/data')
@authorize("system:finance_statistics:staff_wage:main")
def data():
    """ 获取工资信息 """
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')
    dept_id = current_user.dept_id
    staff_id = request.args.get('staffId', type=int)
    role_id = request.args.get('roleId', type=int)
    year_month = request.args.get('yearMonth', type=str)

    query = db.session.query(FactoryFinanceStaff).filter(
        FactoryFinanceStaff.dept_id == dept_id
    )
    if staff_id:
        query = query.filter(FactoryFinanceStaff.staff_id == staff_id)
    if role_id:
        query = query.filter(FactoryFinanceStaff.role_id == role_id)
    if year_month:
        year = year_month[:4]
        month = year_month[5:]
        query = query.filter(
            FactoryFinanceStaff.year == year,
            FactoryFinanceStaff.month == month
        )
    query_finance_staff = query.order_by(
        FactoryFinanceStaff.year.desc(),
        FactoryFinanceStaff.month.desc()
    ).layui_paginate()

    schema = FactoryFinanceStaffSchema(many=True)
    result = schema.dump(query_finance_staff)
    salary_type_map = {
        "fixed": "固定薪资",
        "base_plus_commission": "底薪+提成",
        "piecework": "计件"
    }
    for item in result:
        item['salary_type'] = salary_type_map.get(item['salary_type'], item['salary_type'])
    db.session.close()
    return table_api(data=result, count=query_finance_staff.total)


# def get_date_range(year, month):
#     """
#     获取指定年月的开始日期和结束日期
#     :param year: 年份
#     :param month: 月份
#     :return: 开始日期和结束日期
#     """
#     if month == 1:
#         year -= 1
#         month = 12
#     else:
#         month -= 1
#     start_date = datetime.datetime(year, month, 1)
#     end_date = datetime.datetime(year if month != 12 else year + 1, month + 1 if month != 12 else 1, 1)
#     return start_date, end_date


def get_finance_subsidy(dept_id):
    """
    获取当前部门的补贴信息
    :param dept_id: 部门ID
    :return: 补贴信息
    """
    return db.session.query(FactoryFinanceSubsidy).filter(
        FactoryFinanceSubsidy.dept_id == dept_id,
        FactoryFinanceSubsidy.is_reference == 1
    ).first()



def calculate_salary(staff, finance_subsidy, start_date, end_date):
    """
    计算员工工资
    :param staff: 员工信息
    :param finance_subsidy: 补贴信息
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 工资信息
    """
    staff_id = staff.id
    staff_role_id = staff.role_id
    salary_type = staff.salary_type
    rent_subsidy = finance_subsidy.rent_subsidy if finance_subsidy else 0.00
    life_subsidy = finance_subsidy.life_subsidy if finance_subsidy else 0.00
    other_subsidy = finance_subsidy.other_subsidy if finance_subsidy else 0.00

    if salary_type == 'fixed' or salary_type == 'base_plus_commission':
        base_salary = staff.base_salary
        finance_staff = db.session.query(FactoryFinanceStaff).filter_by(
            dept_id=staff.dept_id,
            staff_id=staff_id,
            role_id=staff_role_id,
            year=start_date.year,
            month=start_date.month
        ).first()
        if finance_staff:
            return

        orders = db.session.query(FactoryOrder).filter(
            FactoryOrder.dept_id == staff.dept_id,
            FactoryOrder.is_deleted == 0
        ).first()
        if not orders or not orders.sew_unit_price:
            return fail_api(msg='裁床单价不存在，请联系管理员设置裁床单价')

        performance_salary = 0
        finance_performances = db.session.query(FactoryFinancePerformance).filter(
            FactoryFinancePerformance.dept_id == staff.dept_id,
            FactoryFinancePerformance.staff_id == staff_id,
            FactoryFinancePerformance.role_id == staff_role_id,
            FactoryFinancePerformance.date >= start_date,
            FactoryFinancePerformance.date < end_date
        ).all()
        if finance_performances:
            for finance_performance in finance_performances:
                performance_salary += finance_performance.piece_work_count * orders.sew_unit_price

        salary = base_salary + rent_subsidy + life_subsidy + other_subsidy + performance_salary
        actual_salary = salary

        db.session.add(
            FactoryFinanceStaff(
                dept_id=staff.dept_id,
                staff_id=staff_id,
                role_id=staff_role_id,
                year=start_date.year,
                month=start_date.month,
                piece_work_salary=base_salary,
                performance_salary=performance_salary,
                rent_subsidy=rent_subsidy,
                life_subsidy=life_subsidy,
                other_subsidy=other_subsidy,
                salary=salary,
                actual_salary=actual_salary
            )
        )
    elif salary_type == 'piecework':
        cutting_bed_details = db.session.query(FactoryCuttingBedDetails).filter(
            FactoryCuttingBedDetails.staff_id == staff_id,
            FactoryCuttingBedDetails.delivery_date >= start_date,
            FactoryCuttingBedDetails.delivery_date < end_date,
            FactoryCuttingBedDetails.is_calculated == 0
        ).all()
        if not cutting_bed_details:
            finance_staff = db.session.query(FactoryFinanceStaff).filter_by(
                dept_id=staff.dept_id,
                staff_id=staff_id,
                role_id=staff_role_id,
                year=start_date.year,
                month=start_date.month
            ).first()
            if finance_staff:
                return
            salary = rent_subsidy + life_subsidy + other_subsidy
            db.session.add(
                FactoryFinanceStaff(
                    dept_id=staff.dept_id,
                    staff_id=staff_id,
                    role_id=staff_role_id,
                    year=start_date.year,
                    month=start_date.month,
                    rent_subsidy=rent_subsidy,
                    life_subsidy=life_subsidy,
                    other_subsidy=other_subsidy,
                    performance_salary=0,
                    salary=salary,
                    actual_salary=salary
                )
            )
        else:
            for cutting_bed_detail in cutting_bed_details:
                db.session.query(FactoryCuttingBedDetails).filter_by(id=cutting_bed_detail.id).update(
                    {'is_calculated': True}
                )
                staff_shipment_number = cutting_bed_detail.staff_shipment_number
                cutting_bed_id = cutting_bed_detail.cutting_bed_id
                cutting_beds = db.session.query(FactoryCuttingBed).get(cutting_bed_id)
                orders = db.session.query(FactoryOrder).get(cutting_beds.order_id)
                staff_unit_price = orders.staff_unit_price
                new_performance_salary = staff_unit_price * staff_shipment_number
                finance_staff = db.session.query(FactoryFinanceStaff).filter_by(
                    dept_id=staff.dept_id,
                    staff_id=staff_id,
                    role_id=staff_role_id,
                    year=start_date.year,
                    month=start_date.month
                ).first()
                if finance_staff:
                    performance_salary = finance_staff.performance_salary + new_performance_salary
                    salary = finance_staff.salary + new_performance_salary
                    db.session.query(FactoryFinanceStaff).filter_by(id=finance_staff.id).update(
                        {
                            'salary': salary,
                            'performance_salary': performance_salary,
                            'actual_salary': salary
                        }
                    )
                else:
                    salary = rent_subsidy + life_subsidy + other_subsidy + new_performance_salary
                    db.session.add(
                        FactoryFinanceStaff(
                            dept_id=staff.dept_id,
                            staff_id=staff_id,
                            role_id=staff_role_id,
                            year=start_date.year,
                            month=start_date.month,
                            rent_subsidy=rent_subsidy,
                            life_subsidy=life_subsidy,
                            other_subsidy=other_subsidy,
                            performance_salary=new_performance_salary,
                            salary=salary,
                            actual_salary=salary
                        )
                    )


# 财务统计-员工工资-生产上月工资（接口）
@bp.post('/save')
@authorize("system:finance_statistics:staff_wage:add")
def save():
    """ 保存工资信息 """
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    year, month, start_date, end_date = get_date()
    dept_id = current_user.dept_id

    try:
        all_staff = db.session.query(FactoryStaff).filter_by(
            dept_id=dept_id,
            staff_status='active',
            is_deleted=False
        ).order_by(FactoryStaff.id).all()
        finance_subsidy = get_finance_subsidy(dept_id)
        with db.session.begin_nested():
            for staff in all_staff:
                calculate_salary(staff, finance_subsidy, start_date, end_date)
        db.session.commit()
        return success_api(msg='上月工资信息更新成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='上月工资信息更新失败')
    finally:
        db.session.close()


# 财务统计-员工工资-修改（弹框数据）
@bp.get('/edit/<int:finance_staff_id>')
@authorize("system:finance_statistics:staff_wage:edit")
def edit(finance_staff_id):
    """ 显示编辑页面 """
    finance_staffs = db.session.query(FactoryFinanceStaff).get(finance_staff_id)
    staffs = db.session.query(FactoryStaff).get(finance_staffs.staff_id)
    roles = db.session.query(Role).get(finance_staffs.role_id)
    db.session.close()
    return render_template(
        'system/factory/finance_statistics/staff_wage/edit.html',
        finance_staffs=finance_staffs,
        finance_staff_id=finance_staff_id,
        staffs=staffs,
        roles=roles
    )


# 财务统计-员工工资-修改（接口）
@bp.put('/update')
@authorize("system:finance_statistics:staff_wage:edit")
def update():
    """ 更新工资信息 """
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    req = request.get_json(force=True)
    finance_staff_id = str_escape(req.get('financeStaffId'))
    fields = {
        'rentSubsidy': 'rent_subsidy',
        'lifeSubsidy': 'life_subsidy',
        'otherSubsidy': 'other_subsidy',
        'advanceSalary': 'advance_salary',
        'otherDeduction': 'other_deduction'
    }
    field_values = {field: str_escape(req.get(field)) for field in fields.keys()}

    try:
        finance_staff = db.session.query(FactoryFinanceStaff).get(finance_staff_id)

        if not finance_staff:
            return fail_api(msg='工资信息不存在')

        finance_data = {}
        for req_field, db_field in fields.items():
            field_value = field_values[req_field]
            if field_value:
                finance_data[db_field] = field_value
            else:
                db_value = getattr(finance_staff, db_field, None)
                finance_data[db_field] = db_value if db_value is not None else 0

        salary = float(finance_staff.piece_work_salary) + float(finance_staff.performance_salary) + \
                 float(finance_data['rent_subsidy']) + float(finance_data['life_subsidy']) + float(finance_data['other_subsidy'])
        actual_salary = salary - float(finance_data['advance_salary']) - float(finance_data['other_deduction'])
        finance_data['salary'] = salary
        finance_data['actual_salary'] = actual_salary

        db.session.query(FactoryFinanceStaff).filter_by(id=finance_staff_id).update(finance_data)
        db.session.commit()
        return success_api(msg='工资信息更新成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='工资信息更新失败')
    finally:
        db.session.close()


# 财务统计-员工工资-设置补贴（弹框数据）
@bp.get('/subsidy')
@authorize("system:finance_statistics:staff_wage:subsidy")
def subsidy():
    """ 显示补贴信息 """
    return render_template('system/factory/finance_statistics/staff_wage/subsidy.html')


# 财务统计-员工工资-设置补贴（接口）
@bp.put('/subsidy_update')
@authorize("system:finance_statistics:staff_wage:subsidy")
def subsidy_update():
    """ 更新补贴信息 """
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    req = request.get_json(force=True)
    rent_subsidy = str_escape(req.get('rentSubsidy'))
    life_subsidy = str_escape(req.get('lifeSubsidy'))
    other_subsidy = str_escape(req.get('otherSubsidy'))
    if not rent_subsidy and not life_subsidy and not other_subsidy:
        return fail_api(msg='补助金额不能全部为空，至少要有一个补助金额')
    subsidy_data = {}
    if rent_subsidy:
        subsidy_data['rent_subsidy'] = rent_subsidy
    if life_subsidy:
        subsidy_data['life_subsidy'] = life_subsidy
    if other_subsidy:
        subsidy_data['other_subsidy'] = other_subsidy

    dept_id = current_user.dept_id
    subsidy_data['dept_id'] = dept_id
    try:
        finance_subsidy = db.session.query(FactoryFinanceSubsidy).filter_by(dept_id=dept_id, is_reference=True).first()
        if not finance_subsidy:
            db.session.add(FactoryFinanceSubsidy(**subsidy_data))
        else:
            db.session.query(FactoryFinanceSubsidy).filter_by(dept_id=dept_id, is_reference=True).update(
                {"is_reference": False})
            if finance_subsidy.rent_subsidy and not rent_subsidy:
                subsidy_data['rent_subsidy'] = finance_subsidy.rent_subsidy
            if finance_subsidy.life_subsidy and not life_subsidy:
                subsidy_data['life_subsidy'] = finance_subsidy.life_subsidy
            if finance_subsidy.other_subsidy and not other_subsidy:
                subsidy_data['other_subsidy'] = finance_subsidy.other_subsidy
            db.session.add(FactoryFinanceSubsidy(**subsidy_data))
        db.session.commit()
        return success_api(msg='补助信息更新成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='补助信息更新失败')
    finally:
        db.session.close()


# 财务统计-员工工资-员工绩效（弹框数据）
@bp.get('/performance/<int:finance_staff_id>')
@authorize("system:finance_statistics:staff_wage:performance")
def performance(finance_staff_id):
    """ 显示员工绩效信息 """
    finance_staff = db.session.query(FactoryFinanceStaff).get(finance_staff_id)
    staffs = db.session.query(FactoryStaff).get(finance_staff.staff_id)
    roles = db.session.query(Role).get(finance_staff.role_id)
    db.session.close()
    return render_template(
        'system/factory_finance_staff/performance.html',
        finance_staff=finance_staff,
        staffs=staffs,
        roles=roles
    )


# 财务统计-员工工资-员工绩效（接口）
@bp.post('/performance_save')
@authorize("system:finance_statistics:staff_wage:performance")
def performance_save():
    """ 保存员工绩效信息 """
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    dept_id = current_user.dept_id
    req = request.get_json(force=True)
    staff_id = str_escape(req.get('staffId'))
    role_id = str_escape(req.get('roleId'))
    date = str_escape(req.get('date'))
    piece_work_count = str_escape(req.get('pieceWorkCount'))
    year = date.split('-')[0]
    month = date.split('-')[1]
    if not date:
        return fail_api(msg='日期不能为空')
    if not piece_work_count:
        return fail_api(msg='件数不能为空')
    performance_data = FactoryFinancePerformance(
        dept_id=dept_id,
        staff_id=staff_id,
        role_id=role_id,
        date=date,
        piece_work_count=piece_work_count
    )
    try:
        performances = db.session.query(FactoryFinancePerformance).filter_by(
            dept_id=dept_id,
            staff_id=staff_id,
            role_id=role_id,
            date=date
        ).first()
        if performances:
            return fail_api(msg='该员工【{}】的绩效信息已存在'.format(date))
        db.session.add(performance_data)
        orders = db.session.query(FactoryOrder).filter(FactoryOrder.dept_id == dept_id).limit(1).first()
        if not orders:
            return fail_api(msg='该工厂没有订单信息，请先创建订单信息')
        finance_staffs = db.session.query(FactoryFinanceStaff).filter_by(
            dept_id=dept_id,
            staff_id=staff_id,
            role_id=role_id,
            year=year,
            month=month
        ).first()
        if not finance_staffs:
            return fail_api(msg='该员工【{}】的工资信息不存在'.format(staff_id))
        performance_salary = int(piece_work_count) * float(orders.sew_unit_price) + float(finance_staffs.performance_salary)
        salary = float(finance_staffs.salary) + performance_salary
        actual_salary = salary - float(finance_staffs.advance_salary) - float(finance_staffs.other_deduction)
        db.session.query(FactoryFinanceStaff).filter_by(id=finance_staffs.id).update(
            {
                'performance_salary': performance_salary,
                'salary': salary,
                'actual_salary': actual_salary
            }
        )
        db.session.commit()
        return success_api(msg='绩效信息保存成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='绩效信息保存失败')
    finally:
        db.session.close()


# 财务统计-员工工资-设置烫工单价（弹框数据）
@bp.get('/set_unit_price')
@authorize("system:finance_statistics:staff_wage:set_unit_price")
def set_unit_price():
    orders = db.session.query(FactoryOrder).filter_by(dept_id=current_user.dept_id).limit(1).first()
    return render_template('system/factory/finance_statistics/staff_wage/set_unit_price.html', orders=orders)


# 财务统计-员工工资-设置烫工单价（接口）
@bp.put('/set_unit_price_update')
@authorize("system:finance_statistics:staff_wage:set_unit_price")
def set_unit_price_update():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')
    dept_id = current_user.dept_id
    req = request.get_json(force=True)
    sew_unit_price = str_escape(req.get('sewUnitPrice'))
    if not sew_unit_price:
        return fail_api(msg='烫工单价不能为空')
    try:
        orders = db.session.query(FactoryOrder).filter_by(dept_id=dept_id).all()
        for order in orders:
            if order.sew_unit_price is None:
                db.session.query(FactoryOrder).filter_by(id=order.id).update(
                    {"sew_unit_price": sew_unit_price}
                )
        db.session.commit()
        return success_api(msg='烫工单价设置成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='烫工单价设置失败')
    finally:
        db.session.close()
