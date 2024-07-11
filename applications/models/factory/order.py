# -*- coding: utf-8 -*-
# @Time    : 2024/7/3 22:39
# @File    : order.py
# @Software: PyCharm
# @Author  : Roc
import datetime
from applications.extensions import db


class FactoryOrder(db.Model):
    __tablename__ = 'factory_order'
    __table_args__ = {'comment': '工厂订单表'}
    id = db.Column(db.Integer, primary_key=True, comment='订单唯一标识ID')
    product_model_number = db.Column(db.String(50), nullable=False, comment='产品款号')
    order_status = db.Column(db.String(50), nullable=False, default='Submitted',
                             comment='订单状态(订单提交：Submitted；裁剪分包：Cutting；裁剪完成：CuttingCompleted；'
                                     '缝制生产：Sewing；包装发货：Packing；完成订单：Completed)')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='所属工厂部门ID', nullable=False)
    order_client_id = db.Column(db.Integer, db.ForeignKey('factory_client.id'), comment='订单客户ID', nullable=False)
    order_client_number = db.Column(db.Integer, comment='订单下单数量')
    order_client_unit_price = db.Column(db.Numeric(15, 2), default=None, comment='订单下单单价')
    order_shipment_number = db.Column(db.Integer, comment='出货数量')
    staff_unit_price = db.Column(db.Numeric(15, 2), comment='员工单价')
    sew_unit_price = db.Column(db.Numeric(15, 2), comment='烫工单价')
    order_user_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), comment='创建订单的用户ID', nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, comment='是否已删除')
    order_date = db.Column(db.DateTime, comment='下单日期')
    cutting_date = db.Column(db.DateTime, comment='裁货时间')
    delivery_date = db.Column(db.DateTime, comment='货期/预计交货日期')
    shipment_date = db.Column(db.DateTime, comment='发货日期')
    is_repayment = db.Column(db.Boolean, default=False, comment='是否回款')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='记录创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='记录更新时间')
    order_details = db.relationship('FactoryOrderDetails', backref='factory_order', lazy='select')


class FactoryOrderDetails(db.Model):
    __tablename__ = 'factory_order_details'
    __table_args__ = {'comment': '工厂订单外发客户详情表'}
    id = db.Column(db.Integer, primary_key=True, comment='订单详情唯一标识ID')
    external_client_number = db.Column(db.Integer, comment='给外发客户的数量')
    external_client_shipment_number = db.Column(db.Integer, comment='外发客户交货的数量')
    external_client_unit_price = db.Column(db.Numeric(15, 2), default=None, comment='外发客户单价')
    external_client_id = db.Column(db.Integer, db.ForeignKey('factory_client.id'), comment='外发客户ID', nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('factory_order.id'), comment='关联的订单ID', nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='订单详情创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='订单详情更新时间')
    external_client = db.relationship('FactoryClient', foreign_keys='FactoryOrderDetails.external_client_id')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = {'comment': '工厂订单款号的颜色、尺码、数量详情表'}
    id = db.Column(db.Integer, primary_key=True, comment='订单关于颜色、尺码、数量唯一标识ID')
    order_id = db.Column(
        db.Integer, db.ForeignKey('factory_order.id'), nullable=False, comment='关联的订单ID'
    )
    product_model_id = db.Column(db.Integer, db.ForeignKey('product_models.id'), nullable=False, comment='关联的尺码ID')
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=False, comment='关联的颜色ID')
    quantity = db.Column(db.Integer, nullable=False, default=0, comment='该尺码和颜色的数量')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='更新时间')
    product_models = db.relationship('ProductModel', backref=db.backref('order_items', lazy='dynamic'))
    colors = db.relationship('Color', backref=db.backref('order_items', lazy='dynamic'))


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    __table_args__ = {'comment': '工厂订单状态变更历史记录表'}
    id = db.Column(db.Integer, primary_key=True, comment='订单状态历史记录ID')
    factory_order_id = db.Column(db.Integer, db.ForeignKey('factory_order.id'), nullable=False, comment='关联的订单ID')
    previous_status = db.Column(db.String(50), nullable=False, comment='状态变更前的状态')
    new_status = db.Column(db.String(50), nullable=False, comment='状态变更后的新状态')
    status_changed_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='状态变更时间')
    changed_by = db.Column(db.String(50), comment='状态变更操作员')
    reason = db.Column(db.Text, comment='状态变更原因')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now,
                            comment='更新时间')
