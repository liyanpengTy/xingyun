# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 0:00
# @File    : size.py
# @Software: PyCharm
# @Author  : Roc
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models import ProductModel


class ProductModelSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = ProductModel
        include_fk = True