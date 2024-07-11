# -*- coding: utf-8 -*-
# @Time    : 2024/7/5 1:33
# @File    : cutting_bed.py
# @Software: PyCharm
# @Author  : Roc

import datetime
from applications.extensions import db


class FactoryCuttingBed(db.Model):
    __tablename__ = 'factory_cutting_bed'
    __table_args__ = {'comment': '裁床单'}
    id = db.Column(db.Integer, primary_key=True, comment='裁床单唯一标识ID')
    bed_number = db.Column(db.String(50), nullable=False, comment='床次')
    bundle_code_number = db.Column(db.Integer, comment='扎号总数量')
    units_number = db.Column(db.Integer, comment='件数总数量')
    is_bed = db.Column(db.Integer, comment='是否关联床次')
    parent_level_id = db.Column(db.Integer, comment='关联裁单ID')
    parent_level_number = db.Column(db.String(50), comment='关联床次/父级床次')
    order_id = db.Column(db.Integer, db.ForeignKey('factory_order.id'), comment='订单ID')
    staff_id = db.Column(db.Integer, db.ForeignKey('factory_staff.id'), comment='裁货人ID', nullable=False)
    is_completed = db.Column(db.Boolean, default=False, comment='是否完成')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='记录创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='记录更新时间')
    order = db.relationship('FactoryOrder', backref='factory_cutting_bed', lazy='joined')
    staff = db.relationship('FactoryStaff', backref='factory_cutting_bed', lazy='joined')


class FactoryCuttingBedDetails(db.Model):
    __tablename__ = 'factory_cutting_bed_details'
    __table_args__ = {'comment': '裁床单详细'}
    id = db.Column(db.Integer, primary_key=True, comment='裁床单详细唯一标识ID')
    cutting_bed_id = db.Column(db.Integer, db.ForeignKey('factory_cutting_bed.id'), comment='关联裁床单ID', nullable=False)
    bundle_code = db.Column(db.Integer, comment='扎号')
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=False, comment='关联的颜色ID')
    product_model_id = db.Column(db.Integer, db.ForeignKey('product_models.id'), nullable=False, comment='关联的尺码ID')
    quantity = db.Column(db.Integer, comment='数量')
    staff_id = db.Column(db.Integer, db.ForeignKey('factory_staff.id'), comment='员工ID')
    staff_shipment_number = db.Column(db.Integer, comment='员工交货数量')
    dispatch_date = db.Column(db.DateTime, comment='派发日期')
    delivery_date = db.Column(db.DateTime, comment='交货日期')
    is_calculated = db.Column(db.Boolean, default=False, comment='是否计算过价格')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='记录创建时间')
    update_time = db.Column(
        db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='记录更新时间'
    )
    product_models = db.relationship('ProductModel', backref='factory_cutting_bed_details', lazy='joined')
    colors = db.relationship('Color', backref='factory_cutting_bed_details', lazy='joined')
    cutting_beds = db.relationship('FactoryCuttingBed', backref='factory_cutting_bed_details', lazy='joined')
    staff = db.relationship('FactoryStaff', backref='factory_cutting_bed_details', lazy='joined')


class FactoryOutsource(db.Model):
    __tablename__ = 'factory_outsource'
    __table_args__ = {'comment': '厂外协助详情'}
    id = db.Column(db.Integer, primary_key=True, comment='厂外协助唯一标识ID')
    order_id = db.Column(db.Integer, db.ForeignKey('factory_order.id'), comment='订单ID')
    client_id = db.Column(db.Integer, db.ForeignKey('factory_client.id'), comment='客户ID')
    outsource_type = db.Column(db.String(50), comment='协助类型')
    unit_price = db.Column(db.Float, comment='单价')
    quantity = db.Column(db.Integer, comment='数量')
    is_delete = db.Column(db.Boolean, default=False, comment='是否删除')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='记录创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='记录更新时间')
    order = db.relationship('FactoryOrder', backref='factory_outsource', lazy='joined')
    client = db.relationship('FactoryClient', backref='factory_outsource', lazy='joined')

