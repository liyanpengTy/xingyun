# -*- coding: utf-8 -*-
# @Time    : 2024/7/6 0:12
# @File    : finance.py
# @Software: PyCharm
# @Author  : Roc
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models.factory.finance import *
from marshmallow import fields


class FactoryFinanceStaffSchema(SQLAlchemyAutoSchema):
    staff_name = fields.String(attribute="staff.staff_name")
    role_name = fields.String(attribute="role.name")
    salary_type = fields.String(attribute="staff.salary_type")

    class Meta:
        model = FactoryFinanceStaff
        load_instance = True
        fields = [
            "id", "year", "month", "staff_name", "role_name", "salary_type", "rent_subsidy", "life_subsidy",
            "other_subsidy", "piece_work_salary", "performance_salary", "salary", "advance_salary", "other_deduction", "actual_salary"
        ]


class FactoryFinanceSubsidySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FactoryFinanceSubsidy
        load_instance = True
        # fields = []


class FactoryFinancePerformanceSchema(SQLAlchemyAutoSchema):
    sew_unit_price = fields.String(attribute="dept.factory_orders.sew_unit_price")

    class Meta:
        model = FactoryFinancePerformance
        load_instance = True
        fields = [
            "id", "date", "piece_work_count", "total_price", "sew_unit_price"
        ]


class FactoryFinanceOtherSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FactoryFinanceOther
        load_instance = True
        # fields = []


class FactoryFinanceOtherDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FactoryFinanceOtherDetail
        load_instance = True
        fields = [
            "id", "date", "name", "category", "unit_price", "quantity", "unit", "amount"
        ]


class FactoryFinanceClientSchema(SQLAlchemyAutoSchema):
    client_name = fields.String(attribute="client.client_name")
    client_type = fields.String(attribute="client.client_type")

    class Meta:
        model = FactoryFinanceClient
        load_instance = True
        fields = [
            "id", "year", "month", "client_name", "client_type", "receivable", "received", "payable", "paid", "balance", "is_settle"
        ]


class FactoryFinanceClientDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FactoryFinanceClientDetail
        load_instance = True
        # fields = []


class IncomeExpenitureStatisticsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IncomeExpenditureStatistics
        load_instance = True
        # fields = []


class OtherIncomeDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = OtherIncomeDetail
        load_instance = True
        # fields = []