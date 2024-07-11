# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 21:18
# @File    : client_management.py
# @Software: PyCharm
# @Author  : Roc

from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import Dept, FactoryClient
from applications.schemas import FactoryClientSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user

bp = Blueprint('client_management', __name__, url_prefix='/factory/client_management')


# 用户管理
@bp.get('/')
@authorize("system:client:main")
def main():
    return render_template('system/factory/client_management/main.html')


#   用户分页查询
@bp.get('/data')
@authorize("system:client:main")
def data():
    # 获取请求参数
    client_name = str_escape(request.args.get('clientName', type=str))
    client_type = str_escape(request.args.get('clientType', type=str))
    client_types = ''
    if client_type == "订单客户":
        client_types = "orderClient"
    elif client_type == "外发客户":
        client_types = "externalClient"
    elif client_type == "协作客户":
        client_types = "partnerClient"
    filters = []
    if client_name:
        filters.append(FactoryClient.client_name.contains(client_name))
    if client_type:
        filters.append(FactoryClient.client_type == client_types)
    dept_id = current_user.dept_id
    filters.append(FactoryClient.dept_id == dept_id)
    filters.append(FactoryClient.is_deleted != 1)

    query = db.session.query(FactoryClient).options(
        db.joinedload(FactoryClient.dept)
    ).filter(*filters).layui_paginate()
    db.session.close()
    schema = FactoryClientSchema(many=True)
    result = schema.dump(query)
    for item in result:
        if item['client_type'] == "orderClient":
            item['client_type'] = "订单客户"
        elif item['client_type'] == "externalClient":
            item['client_type'] = "外发客户"
        elif item['client_type'] == "partnerClient":
            item['client_type'] = "协作客户"

    return table_api(data=result, count=query.total)


# 客户增加
@bp.get('/add')
@authorize("system:client:add", log=True)
def add():
    dept = db.session.query(Dept).all()
    db.session.close()
    return render_template('system/factory/client_management/add.html', depts=dept)


@bp.post('/save')
@authorize("system:client:add", log=True)
def save():
    req = request.get_json(force=True)
    # 验证是否登录
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")
    # 获取当前登录用户的部门/工厂id
    dept_id = current_user.dept_id
    client_name = str_escape(req.get('clientName'))
    client_phone = str_escape(req.get('clientPhone'))
    client_type = str_escape(req.get('clientType'))
    if not client_name:
        return fail_api(msg="客户姓名不能为空")
    if not client_phone:
        return fail_api(msg="手机号不能为空")
    if not client_type:
        return fail_api(msg="客户类型不能为空")
    if not Dept.query.get(dept_id):
        return fail_api(msg="无效的部门Id")

    new_client = FactoryClient(
        client_name=client_name,
        client_phone=client_phone,
        client_type=client_type,
        dept_id=dept_id
    )
    db.session.add(new_client)
    try:
        db.session.commit()
        return success_api(msg="新增客户成功")
    except Exception as e:
        db.session.rollback()
        return fail_api(msg="保存失败： " + str(e))
    finally:
        db.session.close()


# 删除客户
@bp.delete('/remove/<int:id>')
@authorize("system:client:remove", log=True)
def delete(id):
    client = FactoryClient.query.get(id)
    if client is None:
        return fail_api(msg="未找到客户信息")
    client.is_deleted = True
    db.session.commit()
    if client.is_deleted:
        return success_api(msg="删除成功")
    else:
        return fail_api(msg="删除失败")


#  编辑客户-获取角色名称
@bp.get('/edit/<int:id>')
@authorize("system:client:edit", log=True)
def edit(id):
    client = db.session.query(FactoryClient).get(id)
    return render_template('system/factory/client_management/edit.html', client=client)


#  编辑客户
@bp.put('/update')
@authorize("system:client:edit", log=True)
def update():
    req_json = request.get_json(force=True)
    client_id = str_escape(req_json.get("clientId"))
    client_data = {
        'client_name': str_escape(req_json.get('clientName')),
        'client_phone': str_escape(req_json.get('clientPhone')),
        'client_type': str_escape(req_json.get('client_type')),
    }
    try:
        client = db.session.query(FactoryClient).get(client_id)
        if not client:
            return fail_api(msg="客户不存在")
        db.session.query(FactoryClient).filter_by(id=client_id).update(client_data)
        db.session.commit()
        return success_api(msg="客户信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败：" + str(e))
    finally:
        db.session.close()
