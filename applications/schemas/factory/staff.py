# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 21:51
# @File    : staff.py
# @Software: PyCharm
# @Author  : Roc
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models import FactoryStaff
from marshmallow import fields


class FactoryStaffSchema(SQLAlchemyAutoSchema):
    role_name = fields.String(attribute='role.name')
    class Meta:
        model = FactoryStaff
        include_fk = True
        load_instance = True
        include_relationships = True
        fields = [
            "id", "staff_name", "work_number", "gender", "staff_phone", "role_name",
            "salary_type", "base_salary", "enable", "staff_type"
        ]