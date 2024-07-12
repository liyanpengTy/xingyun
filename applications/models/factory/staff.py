# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 21:50
# @File    : staff.py
# @Software: PyCharm
# @Author  : Roc
import datetime
from flask_login import UserMixin
from applications.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class FactoryStaff(db.Model, UserMixin):
    __tablename__ = 'factory_staff'
    __table_args__ = {'comment': '工厂员工表'}
    id = db.Column(db.Integer, primary_key=True, comment='员工Id')
    username = db.Column(db.String(20), nullable=False, comment='账号')
    staff_name = db.Column(db.String(20), comment='员工姓名')
    work_number = db.Column(db.String(50), nullable=False, unique=False, comment='工号')
    gender = db.Column(db.Boolean, comment='性别：【1-男，0-女】')
    staff_phone = db.Column(db.String(20), comment='联系电话')
    salary_type = db.Column(db.String(50), comment='薪资类型(fixed：固定薪资；base_plus_commission：底薪+提成；piecework：计件工资)')
    enable = db.Column(db.Integer, default=1, comment='在职状态(1:在职；0：离职)')
    base_salary = db.Column(db.Numeric(15, 2), default=None, comment='固定金额的底薪')
    password_hash = db.Column(db.String(128), nullable=False, comment='哈希密码')
    dept_id = db.Column(db.Integer, db.ForeignKey('admin_dept.id'), comment='工厂Id，admin_dept表', nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), comment='用户Id，admin_user表')
    role_id = db.Column(db.Integer, db.ForeignKey('admin_role.id'), comment='角色Id，admin_role表')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否删除：【0-否，1-是】')
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    role = db.relationship('Role', backref=db.backref('factory_staff', lazy='dynamic'))
    dept = db.relationship('Dept', backref=db.backref('factory_staff', lazy='dynamic'))
    # 唯一约束条件dept_id与work_number 一起
    __table_args__ = (db.UniqueConstraint('dept_id', 'work_number', name='uniq_work_number_per_dept'),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)