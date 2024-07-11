# -*- coding: utf-8 -*-
# @Time    : 2024/7/3 22:50
# @File    : client.py
# @Software: PyCharm
# @Author  : Roc
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models import FactoryClient


class FactoryClientSchema(SQLAlchemyAutoSchema):

    class Meta:
        model = FactoryClient
        include_fk = True
        load_instance = True
        include_relationships = True
        fields = ["id", "client_name", "client_type", "client_phone"]