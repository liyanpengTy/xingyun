# -*- coding: utf-8 -*-
# @Time    : 2024/7/3 23:58
# @File    : size.py
# @Software: PyCharm
# @Author  : Roc
import datetime
from applications.extensions import db


class ProductModel(db.Model):
    __tablename__ = 'product_models'
    __table_args__ = {'comment': '款号型号表'}
    id = db.Column(db.Integer, primary_key=True, comment='型号唯一标识ID')
    size = db.Column(db.String(50), nullable=False, comment='型号或尺码')
    description = db.Column(db.Text, comment='描述')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='部门id', nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, comment='是否已删除')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')