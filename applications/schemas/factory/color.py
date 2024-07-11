# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 0:03
# @File    : color.py
# @Software: PyCharm
# @Author  : Roc
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models import Color


class ColorSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = Color
        include_fk = True