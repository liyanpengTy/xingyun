# -*- coding: utf-8 -*-
# @Time    : 2024/7/6 0:12
# @File    : finance.py
# @Software: PyCharm
# @Author  : Roc

import datetime
from applications.extensions import db


class FactoryFinanceStaff(db.Model):
    __tablename__ = 'factory_finance_staff'
    __table_args__ = {'comment': '财务统计-员工工资'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂ID')
    staff_id = db.Column(db.Integer, db.ForeignKey('factory_staff.id'), comment='员工ID')
    role_id = db.Column(db.Integer, db.ForeignKey('admin_role.id'), comment='角色/职位ID')
    year = db.Column(db.Integer, comment='年份')
    month = db.Column(db.Integer, comment='月份')
    # 基本工资
    piece_work_salary = db.Column(db.Numeric(15, 2), default=0.00, comment='基本工资')
    # 绩效工资
    performance_salary = db.Column(db.Numeric(15, 2), default=0.00, comment='绩效工资')
    rent_subsidy = db.Column(db.Numeric(15, 2), default=0.00, comment='房租补助')
    life_subsidy = db.Column(db.Numeric(15, 2), default=0.00, comment='生活补助')
    other_subsidy = db.Column(db.Numeric(15, 2), default=0.00, comment='其他补助')
    salary = db.Column(db.Numeric(15, 2), comment='应发工资')
    advance_salary = db.Column(db.Numeric(15, 2), default=0.00, comment='预支工资')
    other_deduction = db.Column(db.Numeric(15, 2), default=0.00, comment='其他扣除')
    actual_salary = db.Column(db.Numeric(15, 2), comment='实发工资')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间'
    )
    dept = db.relationship('Dept', backref='finance_staff', lazy='joined')
    staff = db.relationship('FactoryStaff', backref='finance_staff', lazy='joined')
    role = db.relationship('Role', backref='finance_staff', lazy='joined')


class FactoryFinanceSubsidy(db.Model):
    __tablename__ = 'factory_finance_subsidy'
    __table_args__ = {'comment': '财务统计-补贴'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂ID')
    rent_subsidy = db.Column(db.Numeric(15, 2), comment='房租补助')
    life_subsidy = db.Column(db.Numeric(15, 2), comment='生活补助')
    other_subsidy = db.Column(db.Numeric(15, 2), comment='其他补助')
    is_reference = db.Column(db.Boolean, default=True, comment='是否引用')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间'
    )
    dept = db.relationship('Dept', backref='finance_subsidy', lazy='joined')


class FactoryFinancePerformance(db.Model):
    __tablename__ = 'factory_finance_performance'
    __table_args__ = {'comment': '财务统计-绩效'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂ID')
    staff_id = db.Column(db.Integer, db.ForeignKey('factory_staff.id'), comment='员工ID')
    role_id = db.Column(db.Integer, db.ForeignKey('admin_role.id'), comment='角色/职位ID')
    date = db.Column(db.Date, comment='日期')
    piece_work_count = db.Column(db.Integer, default=0, comment='件数')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间'
    )
    dept = db.relationship('Dept', backref='finance_performance', lazy='joined')
    staff = db.relationship('FactoryStaff', backref='finance_performance', lazy='joined')
    role = db.relationship('Role', backref='finance_performance', lazy='joined')


class FactoryFinanceOther(db.Model):
    __tablename__ = 'factory_finance_other'
    __table_args__ = {'comment': '财务统计-其它开销'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂ID')
    year = db.Column(db.Integer, comment='年份')
    month = db.Column(db.Integer, comment='月份')
    detail_count = db.Column(db.Integer, default=0, comment='明细数量')
    total_amount = db.Column(db.Numeric(15, 2), default=0.00, comment='总金额')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间'
    )
    dept = db.relationship('Dept', backref='finance_other', lazy='joined')


class FactoryFinanceOtherDetail(db.Model):
    __tablename__ = 'factory_finance_other_detail'
    __table_args__ = {'comment': '财务统计-其它开销明细'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    other_id = db.Column(db.Integer, db.ForeignKey('factory_finance_other.id'), comment='其它开销ID')
    date = db.Column(db.Date, comment='日期')
    name = db.Column(db.String(255), comment='名称')
    category = db.Column(db.String(255), comment='类别')
    unit_price = db.Column(db.Numeric(15, 2), default=0.00, comment='单价')
    quantity = db.Column(db.Integer, default=0, comment='数量')
    unit = db.Column(db.String(255), comment='单位')
    amount = db.Column(db.Numeric(15, 2), default=0.00, comment='金额')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间'
    )
    other = db.relationship('FactoryFinanceOther', backref='finance_other_detail', lazy='joined')


class FactoryFinanceClient(db.Model):
    __tablename__ = 'factory_finance_client'
    __table_args__ = {'comment': '财务统计-客户回款'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂ID')
    client_id = db.Column(db.Integer, db.ForeignKey('factory_client.id'), comment='客户ID')
    year = db.Column(db.Integer, comment='年份')
    month = db.Column(db.Integer, comment='月份')
    receivable = db.Column(db.Numeric(15, 2), comment='应收款金额')
    received = db.Column(db.Numeric(15, 2), comment='已收款金额')
    payable = db.Column(db.Numeric(15, 2), comment='应付款金额')
    paid = db.Column(db.Numeric(15, 2), comment='已付款金额')
    balance = db.Column(db.Numeric(15, 2), comment='差额')
    is_settle = db.Column(db.Boolean, default=False, comment='是否结算')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='更新时间')
    dept = db.relationship('Dept', backref='finance_client', lazy='joined')
    client = db.relationship('FactoryClient', backref='finance_client', lazy='joined')


class FactoryFinanceClientDetail(db.Model):
    __tablename__ = 'factory_finance_client_detail'
    __table_args__ = {'comment': '财务统计-客户回款明细'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    finance_client_id = db.Column(db.Integer, db.ForeignKey('factory_finance_client.id'), comment='客户回款ID')
    date = db.Column(db.Date, comment='日期')
    contract_no = db.Column(db.String(255), comment='款号')
    order_count = db.Column(db.Integer, comment='订单数量')
    order_shipment_number = db.Column(db.Integer, comment='出货数量')
    order_unit_price = db.Column(db.Numeric(15, 2), comment='订单单价')
    external_number = db.Column(db.Integer, comment='发货数量')
    external_shipment_number = db.Column(db.Integer, comment='交货数量')
    external_unit_price = db.Column(db.Numeric(15, 2), comment='发货单价')
    outsource_client_number = db.Column(db.Integer, comment='协助数量')
    outsource_unit_price = db.Column(db.Numeric(15, 2), comment='协助单价')
    amount = db.Column(db.Numeric(15, 2), comment='合计金额')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='更新时间')
    finance_client = db.relationship('FactoryFinanceClient', backref='finance_client_detail', lazy='joined')



class IncomeExpenditureStatistics(db.Model):
    __tablename__ = 'income_expenditure_statistics'
    __table_args__ = {'comment': '财务统计-收支统计'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂ID')
    year = db.Column(db.Integer, comment='年份')
    month = db.Column(db.Integer, comment='月份')
    client_payment_factory = db.Column(db.Numeric(15, 2), default=0.00, comment='客户回款工厂')
    employee_wage_expenses = db.Column(db.Numeric(15, 2), default=0.00, comment='员工工资支出')
    other_expenses = db.Column(db.Numeric(15, 2), default=0.00, comment='其它支出')
    factory_payment_client = db.Column(db.Numeric(15, 2), default=0.00, comment='工厂支付给客户')
    other_income = db.Column(db.Numeric(15, 2), default=0.00, comment='其它收入')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='更新时间')
    dept = db.relationship('Dept', backref='income_expenditure_statistics', lazy='joined')



class OtherIncomeDetail(db.Model):
    __tablename__ = 'other_income_detail'
    __table_args__ = {'comment': '财务统计-收支统计-其他收入明细'}
    id = db.Column(db.Integer, primary_key=True, comment='主键,ID')
    income_id = db.Column(db.Integer, db.ForeignKey('income_expenditure_statistics.id'), comment='收支统计ID')
    date = db.Column(db.Date, comment='日期')
    category = db.Column(db.String(255), comment='类别/名称')
    unit_price = db.Column(db.Numeric(15, 2), default=0.00, comment='单价')
    quantity = db.Column(db.Integer, default=0, comment='数量/重量')
    unit = db.Column(db.String(255), comment='单位')
    amount = db.Column(db.Numeric(15, 2), default=0.00, comment='金额')
    is_delete = db.Column(db.Boolean, default=False, comment='是否删除')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='更新时间')
    income = db.relationship('IncomeExpenditureStatistics', backref='other_income_detail', lazy='joined')