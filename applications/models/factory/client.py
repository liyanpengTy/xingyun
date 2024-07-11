# -*- coding: utf-8 -*-
# @Time    : 2024/7/3 22:48
# @File    : client.py
# @Software: PyCharm
# @Author  : Roc
import datetime
from applications.extensions import db


class FactoryClient(db.Model):
    __tablename__ = 'factory_client'
    __table_args__ = {'comment': '工厂客户表'}
    id = db.Column(db.Integer, primary_key=True, comment='客户Id')
    client_name = db.Column(db.String(20), comment='客户姓名')
    client_type = db.Column(db.String(50), comment='客户类型(订单用户：orderClient；外发客户：'
                                                   'externalClient；协作客户:partnerClient)')
    client_phone = db.Column(db.String(20), comment='联系电话')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂Id，admin_dept表')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否删除：【0-否，1-是】')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    dept = db.relationship('Dept', backref=db.backref('factory_client', lazy='dynamic'))
    factory_orders = db.relationship('FactoryOrder', backref='factory_client', lazy='dynamic')