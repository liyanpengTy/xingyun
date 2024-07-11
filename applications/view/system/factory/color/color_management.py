# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 22:12
# @File    : color_management.py
# @Software: PyCharm
# @Author  : Roc

from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import Color
from applications.schemas import ColorSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user

bp = Blueprint('color_management', __name__, url_prefix='/factory/color_management')


#  颜色管理-主页面
@bp.get('/')
@authorize("system:color:main")
def main():
    return render_template('system/factory/color_management/main.html')


#  颜色管理-列表数据接口
@bp.get('/data')
@authorize("system:color:main")
def data():
    # 获取请求参数
    name = str_escape(request.args.get('name', type=str))
    query = db.session.query(Color)
    if name:
        query = query.filter(Color.name.contains(name))
    if current_user.is_authenticated:
        user_dept_id = current_user.dept_id
        query = query.filter(Color.dept_id == user_dept_id)
    query = query.filter(Color.is_deleted == 0)
    db.session.close()
    colors_with_dept = query.options().all()
    schema = ColorSchema(many=True)
    result = schema.dump(colors_with_dept)
    return table_api(data=result)


#  添加颜色-新增弹框数据
@bp.get('/add')
@authorize("system:color:add", log=True)
def add():
    return render_template('system/factory/color_management/add.html')


#  添加颜色-新增弹框保存
@bp.post('/save')
@authorize("system:color:add", log=True)
def save():
    req = request.get_json(force=True)
    # 验证是否登录
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    # 获取当前登录用户的部门/工厂id
    dept_id = current_user.dept_id
    name = str_escape(req.get('name'))
    code = str_escape(req.get('code'))
    if not name:
        return fail_api(msg="颜色名称不能为空")

    new_color = Color(
        name=name,
        code=code,
        dept_id=dept_id
    )
    try:
        db.session.add(new_color)
        db.session.commit()
        return success_api(msg="保存颜色成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="保存失败")
    finally:
        db.session.close()


# 删除颜色
@bp.delete('/remove/<int:id>')
@authorize("system:color:remove", log=True)
def delete(id):
    color = db.session.query(Color).get(id)
    if color is None:
        return fail_api(msg="未找到颜色信息")
    try:
        color.is_deleted = True
        db.session.commit()
        if color.is_deleted:
            return success_api(msg="删除成功")
        else:
            return fail_api(msg="删除失败")
    finally:
        db.session.close()


#  修改颜色信息-弹框数据
@bp.get('/edit/<int:color_id>')
@authorize("system:color:edit", log=True)
def edit(color_id):
    color = db.session.query(Color).get(color_id)
    db.session.close()
    return render_template('system/factory/color_management/edit.html', color=color)


#  修改颜色信息-弹框保存
@bp.put('/update')
@authorize("system:color:edit", log=True)
def update():
    req_json = request.get_json(force=True)
    color_data = {}
    color_id = str_escape(req_json.get("id"))
    name = str_escape(req_json.get("name"))
    code = str_escape(req_json.get('code'))
    if not name:
        return fail_api(msg="颜色名称不能为空")
    color_data["name"] = name
    color_data["code"] = code
    try:
        color = db.session.query(Color).get(color_id)
        if not color:
            return fail_api(msg="颜色不存在")
        Color.query.filter_by(id=color_id).update(color_data)
        db.session.commit()
        return success_api(msg="更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()
