# -*- coding: utf-8 -*-
# @Time    : 2024/7/12 20:21
# @File    : get_system_name.py
# @Software: PyCharm
# @Author  : Roc

from applications.extensions import db
from applications.models.admin_dept import Dept
from flask_login import current_user

def get_system_name():
    """
    获取当前用户所属部门名称
    :return:
    """
    dept_db = db.session.query(Dept).filter_by(id=current_user.dept_id).first()
    db.session.close()
    SYSTEM_NAME = dept_db.dept_name
    return SYSTEM_NAME