# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 0:01
# @File    : color.py
# @Software: PyCharm
# @Author  : Roc
import datetime
from applications.extensions import db


class Color(db.Model):
    __tablename__ = 'colors'
    __table_args__ = {'comment': '颜色表'}
    id = db.Column(db.Integer, primary_key=True, comment='颜色唯一标识ID')
    name = db.Column(db.String(50), nullable=False, comment='颜色名称')
    code = db.Column(db.String(50), comment='颜色代码')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='部门id', nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, comment='是否已删除')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    __table_args__ = (db.UniqueConstraint('name', 'dept_id'),)