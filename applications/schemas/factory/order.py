# -*- coding: utf-8 -*-
# @Time    : 2024/7/3 22:43
# @File    : order.py
# @Software: PyCharm
# @Author  : Roc
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from applications.models import FactoryOrder, FactoryOrderDetails, OrderStatusHistory, OrderItem
from .client import FactoryClientSchema
from marshmallow import fields


class FactoryOrderDetailsSchema(SQLAlchemyAutoSchema):
    external_client = fields.Nested(FactoryClientSchema)

    class Meta:
        model = FactoryOrderDetails
        include_fk = True
        load_instance = True
        include_relationships = True
        fields = [
            "external_client_name", "external_client_number", "external_client_unit_price",
            "external_client"
        ]


class FactoryOrderSchema(SQLAlchemyAutoSchema):
    client = fields.Nested(FactoryClientSchema)
    order_details = fields.List(fields.Nested(FactoryOrderDetailsSchema), default=[])
    order_client_name = fields.String(attribute='factory_client.client_name')

    class Meta:
        model = FactoryOrder  # table = models.Album.__table__
        include_fk = True  # 序列化阶段是否也一并返回主键
        load_instance = True
        include_relationships = True  # 输出模型对象时同时对外键，是否也一并进行处理
        # exclude = ("is_deleted",)  # 如果需要排除某些字段
        # exclude = ["id","name"] # 排除字段列表
        # excluderelationships = ["client"]  # 排除不序列化的反向关系
        fields = [  # 启动的字段列表
            "id", "product_model_number", "order_client_unit_price", "order_status", "order_client_name",
            "order_client_number", "staff_unit_price", "order_shipment_number", "order_date", "cutting_date",
            "delivery_date", "shipment_date", "client", "order_details", "is_repayment"
        ]


class OrderItemSchema(SQLAlchemyAutoSchema):
    size = fields.String(attribute='product_models.size')
    name = fields.String(attribute='colors.name')

    class Meta:
        model = OrderItem
        include_fk = True
        load_instance = True
        include_relationships = True
        fields = [
            "id", "size", "name", "quantity"
        ]


class OrderStatusHistorySchema(SQLAlchemyAutoSchema):

    class Meta:
        model = OrderStatusHistory
        include_fk = True