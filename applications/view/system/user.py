from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import desc

from applications.common.curd import enable_status, disable_status
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import Role, Dept
from applications.models import User, AdminLog

from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('user', __name__, url_prefix='/user')


# 用户管理
@bp.get('/')
@authorize("system:user:main")
def main():
    return render_template('system/user/main.html')


#   用户分页查询
@bp.get('/data')
@authorize("system:user:main")
def data():
    # 获取请求参数
    real_name = str_escape(request.args.get('realname', type=str))
    username = str_escape(request.args.get('username', type=str))
    user_type = str_escape(request.args.get("userType", type=str))
    dept_id = request.args.get('deptId', type=int)
    # 处理前端传递用户类型
    user_types = ''
    if user_type == "内部用户":
        user_types = "userInternal"
    elif user_type == "外部用户":
        user_types = "userExternal"

    filters = []
    if real_name:
        filters.append(User.realname.contains(real_name))
    if username:
        filters.append(User.username.contains(username))
    if dept_id:
        filters.append(User.dept_id == dept_id)
    if user_type:
        filters.append(User.user_type == user_types)

    query = db.session.query(
        User,
        Dept
    ).filter(*filters).outerjoin(Dept, User.dept_id == Dept.id).layui_paginate()

    return table_api(
        data=[
            {
                'id': user.id,
                'username': user.username,
                'realname': user.realname,
                'phone': user.phone,
                'user_type':"内部用户" if user.user_type == "userInternal" else "外部用户" if user.user_type == "userExternal" else "",
                'enable': user.enable,
                'start_time': user.start_time,
                'end_time': user.end_time,
                'create_at': user.create_at,
                'update_at': user.update_at,
                'dept_name': dept.dept_name if dept else None

            }
            for user, dept in query.items
        ],
        count=query.total
    )


# 用户增加
@bp.get('/add')
@authorize("system:user:add", log=True)
def add():
    roles = Role.query.all()
    return render_template('system/user/add.html', roles=roles)


@bp.post('/save')
@authorize("system:user:add", log=True)
def save():
    req = request.get_json(force=True)
    role_id = req.get("roleId")
    user_name = str_escape(req.get('username'))
    real_name = str_escape(req.get('realName'))
    password = str_escape(req.get('password'))
    phone = str_escape(req.get('phone'))
    user_type = str_escape(req.get('userType'))
    enables = str_escape(req.get('enable'))
    start_time = str_escape(req.get('start_time'))
    end_time = str_escape(req.get('end_time'))

    if not user_name or not real_name or not password:
        return fail_api(msg="账号姓名密码不得为空")

    if bool(User.query.filter_by(username=user_name).count()):
        return fail_api(msg="用户已经存在")

    new_user = User(
        username=user_name,
        realname=real_name,
        phone=phone,
        user_type=user_type,
        enable=enables,
        start_time=start_time,
        end_time=end_time,
        role_id=role_id,
    )

    new_user.set_password(password)
    db.session.add(new_user)

    role = Role.query.get(role_id)
    if role:
        new_user.role.append(role)

    db.session.commit()
    return success_api(msg="新增用户成功")


# 删除用户
@bp.delete('/remove/<int:id>')
@authorize("system:user:remove", log=True)
def delete(id):
    user = User.query.filter_by(id=id).first()
    user.role = []

    res = User.query.filter_by(id=id).delete()
    db.session.commit()
    if not res:
        return fail_api(msg="删除失败")
    return success_api(msg="删除成功")


#  编辑用户-获取角色名称
@bp.get('/edit/<int:id>')
@authorize("system:user:edit", log=True)
def edit(id):
    # user = curd.get_one_by_id(User, id)
    user = User.query.get(id)
    roles = Role.query.all()
    current_user_role_id = user.role_id
    return render_template('system/user/edit.html', user=user, roles=roles, current_user_role_id=current_user_role_id)
    # checked_roles = []
    # for r in user.role:
    #     checked_roles.append(r.id)
    # return render_template('system/user/edit.html', user=user, roles=roles, checked_roles=checked_roles)


#  编辑用户
@bp.put('/update')
@authorize("system:user:edit", log=True)
def update():
    req_json = request.get_json(force=True)
    user_id = str_escape(req_json.get("userId"))
    data = {
        'username': str_escape(req_json.get('username')),
        'realname': str_escape(req_json.get('realName')),
        'phone': str_escape(req_json.get('phone')),
        'dept_id': str_escape(req_json.get('deptId')),
        'role_id': str_escape(req_json.get("roleId")),
        'start_time': str_escape(req_json.get("start_time")),
        'end_time': str_escape(req_json.get("end_time"))
    }
    try:
        user = User.query.get(user_id)
        if not user:
            return fail_api(msg="用户不存在")

        User.query.filter_by(id=user_id).update(data)
        db.session.commit()
        return success_api(msg="用户信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败")


# 个人中心
@bp.get('/center')
@login_required
def center():
    user_info = current_user
    user_logs = AdminLog.query.filter_by(url='/passport/login').filter_by(uid=current_user.id).order_by(
        desc(AdminLog.create_time)).limit(10)
    return render_template('system/user/center.html', user_info=user_info, user_logs=user_logs)


# 修改头像
@bp.get('/profile')
@login_required
def profile():
    return render_template('system/user/profile.html')


# 修改头像
@bp.put('/updateAvatar')
@login_required
def update_avatar():
    url = request.get_json(force=True).get("avatar").get("src")
    r = User.query.filter_by(id=current_user.id).update({"avatar": url})
    db.session.commit()
    if not r:
        return fail_api(msg="出错啦")
    return success_api(msg="修改成功")


# 修改当前用户信息
@bp.put('/updateInfo')
@login_required
def update_info():
    req_json = request.get_json(force=True)
    r = User.query.filter_by(id=current_user.id).update(
        {"realname": req_json.get("realName"), "remark": req_json.get("details")})
    db.session.commit()
    if not r:
        return fail_api(msg="出错啦")
    return success_api(msg="更新成功")


# 修改当前用户密码
@bp.get('/editPassword')
@login_required
def edit_password():
    return render_template('system/user/edit_password.html')


# 修改当前用户密码
@bp.put('/editPassword')
@login_required
def edit_password_put():
    res_json = request.get_json(force=True)
    if res_json.get("newPassword") == '':
        return fail_api("新密码不得为空")
    if res_json.get("newPassword") != res_json.get("confirmPassword"):
        return fail_api("俩次密码不一样")
    user = current_user
    is_right = user.validate_password(res_json.get("oldPassword"))
    if not is_right:
        return fail_api("旧密码错误")
    user.set_password(res_json.get("newPassword"))
    db.session.add(user)
    db.session.commit()
    return success_api("更改成功")


# 启用用户
@bp.put('/enable')
@authorize("system:user:edit", log=True)
def enable():
    _id = request.get_json(force=True).get('userId')
    if _id:
        res = enable_status(model=User, id=_id)
        if not res:
            return fail_api(msg="出错啦")
        return success_api(msg="启动成功")
    return fail_api(msg="数据错误")


# 禁用用户
@bp.put('/disable')
@authorize("system:user:edit", log=True)
def dis_enable():
    _id = request.get_json(force=True).get('userId')
    if _id:
        res = disable_status(model=User, id=_id)
        if not res:
            return fail_api(msg="出错啦")
        return success_api(msg="禁用成功")
    return fail_api(msg="数据错误")
