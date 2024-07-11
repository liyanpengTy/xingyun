# -*- coding: utf-8 -*-
# @Time    : 2024/7/5 1:35
# @File    : cutting_bed.py
# @Software: PyCharm
# @Author  : Roc

from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from ...models.factory.cutting_bed import FactoryCuttingBed, FactoryCuttingBedDetails, FactoryOutsource
from marshmallow import fields


class FactoryCuttingBedSchema(SQLAlchemyAutoSchema):
    product_model_number = fields.String(attribute='order.product_model_number')
    order_status = fields.String(attribute='order.order_status')
    cutting_date = fields.DateTime(attribute='order.cutting_date')
    order_id = fields.Integer(attribute='order.id')
    staff_name = fields.String(attribute='staff.staff_name')

    class Meta:
        model = FactoryCuttingBed
        include_fk = True
        fields = [
            'id', 'bed_number', 'bundle_code_number', 'units_number', 'parent_level_number', 'staff_id',
            'product_model_number', 'staff_name', 'is_completed', 'order_status', 'cutting_date', 'order_id'
        ]


class FactoryCuttingBedDetailsSchema(SQLAlchemyAutoSchema):
    size = fields.String(attribute='product_models.size')
    name = fields.String(attribute='colors.name')
    product_model_number = fields.String(attribute='cutting_beds.order.product_model_number')
    staff_name = fields.String(attribute='staff.staff_name')
    staff_unit_price = fields.String(attribute='cutting_beds.order.staff_unit_price')
    delivery_date = fields.DateTime(attribute='cutting_beds.order.delivery_date')
    total_price = None

    class Meta:
        model = FactoryCuttingBedDetails
        include_fk = True
        fields = [
            "id", "bundle_code", "name", "quantity", "size", "product_model_number", "staff_name",
            "staff_shipment_number", "staff_unit_price", "delivery_date", "total_price"
        ]


class FactoryOutsourceSchema(SQLAlchemyAutoSchema):
    product_model_number = fields.String(attribute='order.product_model_number')
    client_name = fields.String(attribute='client.client_name')

    class Meta:
        model = FactoryOutsource
        include_fk = True
        fields = [
            "id", "outsource_type", "unit_price", "quantity", "product_model_number", "client_name"
        ]
