# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 21:45
# @File    : staff_management.py
# @Software: PyCharm
# @Author  : Roc

from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import Role, Dept, FactoryStaff, User
from applications.schemas import FactoryStaffSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user

bp = Blueprint('staff_management', __name__, url_prefix='/factory/staff_management')


# 员工管理
@bp.get('/')
@authorize("system:staff:main")
def main():
    roles = Role.query.filter(Role.isInternal != "internal").all()
    return render_template('system/factory/staff_management/main.html', roles=roles)


# 员工管理-列表数据
@bp.get('/data')
@authorize("system:staff:main")
def data():
    # 获取请求参数
    staff_ame = str_escape(request.args.get('staffName', type=str))
    role_id = str_escape(request.args.get('roleId', type=str))
    filters = []
    if staff_ame:
        filters.append(FactoryStaff.staff_ame.contains(staff_ame))
    if role_id:
        filters.append(FactoryStaff.role_id == role_id)
    filters.append(FactoryStaff.is_deleted == 0)

    query = FactoryStaff.query.options(
        db.joinedload(FactoryStaff.dept)
    ).filter(*filters).layui_paginate()

    schema = FactoryStaffSchema(many=True)
    result = schema.dump(query)

    salary_type_map = {
        "fixed": "固定薪资",
        "base_plus_commission": "底薪+提成",
        "piecework": "计件"
    }

    # 性别映射
    gender_map = {
        True: "男",
        False: "女"
    }

    # 在职状态映射
    enable_map = {
        1 : "在职",
        0 : "离职"
    }

    for item in result:
        # 映射薪资类型
        item['salary_type'] = salary_type_map.get(item['salary_type'], item['salary_type'])

        # 映射性别
        item['gender'] = gender_map.get(item['gender'], item['gender'])

        # 映射在职状态
        item['enable'] = enable_map.get(item['enable'], item['enable'])

    return table_api(data=result, count=query.total)


# 新增员工-弹框数据
@bp.get('/add')
@authorize("system:staff:add", log=True)
def add():
    # 排除内部角色，外部角色适配职位
    roles = Role.query.filter(Role.isInternal != "internal").all()
    return render_template('system/factory/staff_management/add.html', roles=roles)


# 新增员工-接口
@bp.post('/save')
@authorize("system:staff:add", log=True)
def save():
    req = request.get_json(force=True)
    # 验证是否登录
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    # 获取当前登录用户的部门/工厂id
    dept_id = current_user.dept_id
    staff_name = str_escape(req.get('staffName'))
    work_number = str_escape(req.get('workNumber'))
    staff_phone = str_escape(req.get('staffPhone'))
    password_hash = str_escape(req.get('passwordHash'))
    gender = req.get('gender')
    role_id = str_escape(req.get('roleId'))
    salary_type = str_escape(req.get('salaryType'))
    fixed = str_escape(req.get('fixed'))
    base = str_escape(req.get('base'))
    base_salary = None
    if not staff_name:
        return fail_api(msg="姓名不能为空")
    if not work_number:
        return fail_api(msg="工号不能为空")
    if not staff_phone:
        return fail_api(msg="手机号不能为空")
    if not password_hash:
        return fail_api(msg="登录密码不能为空")
    if not gender:
        return fail_api(msg="性别不能为空")
    if not role_id:
        return fail_api(msg="职位不能为空")
    if not salary_type:
        return fail_api(msg="薪资类型不能为空")
    if fixed:
        base_salary = fixed
    if base:
        base_salary = base
    if gender == "true":
        gender = True
    elif gender == "false":
        gender = False
    try:
        existing_staff = FactoryStaff.query.filter_by(dept_id=dept_id, work_number=work_number).first()
        if existing_staff:
            return fail_api(msg="员工工号重复")

        new_staff = FactoryStaff(
            staff_name=staff_name,
            work_number=work_number,
            staff_phone=staff_phone,
            username=staff_phone,
            gender=gender,
            role_id=role_id,
            salary_type=salary_type,
            base_salary=base_salary,
            dept_id=dept_id
        )
        new_staff.set_password(password_hash)

        if bool(User.query.filter_by(username=staff_phone, enable=1).count()):
            return fail_api(msg="该手机号已被注册，请更换手机号或联系管理员")

        user_db = db.session.query(User).filter_by(dept_id=dept_id, role_id=current_user.role_id).limit(1).first()
        new_user = User(
            username=staff_phone,
            realname=staff_name,
            phone=staff_phone,
            user_type="userExternal",
            enable=1,
            start_time=user_db.start_time,
            end_time=user_db.end_time,
            role_id=role_id,
            dept_id=dept_id
        )
        new_user.set_password(password_hash)
        db.session.add(new_user)
        user_db_new = db.session.query(User).filter_by(
            username=staff_phone
        ).first()
        new_staff.user_id = user_db_new.id
        db.session.add(new_staff)

        role = Role.query.get(role_id)
        if role:
            new_user.role.append(role)

        db.session.commit()
        return success_api(msg="新增员工成功")
    except Exception as e:
        db.session.rollback()
        return fail_api(msg="保存失败： " + str(e))


#  删除员工
@bp.delete('/remove/<int:id>')
@authorize("system:staff:remove", log=True)
def delete(id):
    staff = db.session.query(FactoryStaff).get(id)
    if staff is None:
        return fail_api(msg="未找到员工信息")
    staff.is_deleted = True
    user = db.session.query(User).filter_by(id=staff.user_id).first()
    user.enable = 0
    db.session.commit()
    staff_new = db.session.query(FactoryStaff).get(id)
    db.session.close()
    if staff_new.is_deleted:
        return success_api(msg="删除成功")
    else:
        return fail_api(msg="删除失败")


#  修改员工信息-弹框数据
@bp.get('/edit/<int:id>')
@authorize("system:staff:edit", log=True)
def edit(id):
    staff = FactoryStaff.query.get(id)
    roles = Role.query.filter(Role.isInternal != "internal").all()
    current_role_id = staff.role_id
    salary_type = staff.salary_type
    return render_template(
        'system/factory/staff_management/edit.html',
        roles=roles,
        staff=staff,
        current_role_id=current_role_id,
        salary_type=salary_type
    )


#  修改员工信息-接口
@bp.put('/update')
@authorize("system:staff:edit", log=True)
def update():
    req_json = request.get_json(force=True)
    data = {}
    staff_id = str_escape(req_json.get("staffId"))
    staff_name = str_escape(req_json.get('staffName'))
    if staff_name:
        data['staff_name'] = staff_name
    else:
        return fail_api(msg="姓名不能为空")
    staff_phone = str_escape(req_json.get('staffPhone'))
    if staff_phone:
        data['staff_phone'] = staff_phone
    else:
        return fail_api(msg="手机号不能为空")
    role_id = str_escape(req_json.get("roleId"))
    if role_id:
        data['role_id'] = role_id
    else:
        return fail_api(msg="职位不能为空")
    salary_type = str_escape(req_json.get("salaryType"))
    if salary_type:
        data['salary_type'] = salary_type
    else:
        return fail_api(msg="薪资类型不能为空")
    gender = str_escape(req_json.get('gender'))
    if gender:
        data['gender'] = gender
    else:
        return fail_api(msg="性别不能为空")
    if gender == "true":
        gender = True
    elif gender == "false":
        gender = False
    data["gender"] = gender
    enable = str_escape(req_json.get("enable"))
    data["enable"] = enable
    base_salary = None
    fixed = str_escape(req_json.get("fixed"))
    base = str_escape(req_json.get("base"))
    if salary_type == "piecework":
        base_salary = None
    elif salary_type == "fixed":
        base_salary = fixed
    elif salary_type == "base_plus_commission":
        base_salary = base
    data["base_salary"] = base_salary
    try:
        staff = db.session.query(FactoryStaff).get(staff_id)
        if not staff:
            return fail_api(msg="员工不存在")
        db.session.query(FactoryStaff).filter_by(id=staff_id).update(data)
        new_user = {}
        new_user['username']=staff_phone
        new_user['phone']=staff_phone
        new_user['realname']=staff_name
        new_user['role_id']=role_id
        new_user['enable']=enable
        db.session.query(User).filter_by(id=staff.user_id).update(new_user)
        db.session.commit()
        return success_api(msg="员工信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
