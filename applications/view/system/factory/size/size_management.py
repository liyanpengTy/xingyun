# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 22:33
# @File    : size_management.py
# @Software: PyCharm
# @Author  : Roc

from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import ProductModel
from applications.schemas import ProductModelSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user

bp = Blueprint('size_management', __name__, url_prefix='/factory/size_management')


# 尺码管理-主页面
@bp.get('/')
@authorize("system:size:main")
def main():
    return render_template('system/factory/size_management/main.html')


# 尺码管理-列表数据接口
@bp.get('/data')
@authorize("system:size:main")
def data():
    # 获取请求参数
    size = str_escape(request.args.get('size', type=str))
    query = ProductModel.query
    if size:
        query = query.filter(ProductModel.size.contains(size))
    if current_user.is_authenticated:
        user_dept_id = current_user.dept_id
        # 将部门ID作为筛选条件添加到查询中
        query = query.filter(ProductModel.dept_id == user_dept_id)
    query = query.filter(ProductModel.is_deleted == 0)
    colors_with_dept = query.options().layui_paginate()
    schema = ProductModelSchema(many=True)
    result = schema.dump(colors_with_dept)
    return table_api(data=result, count=colors_with_dept.total)


# 新增尺码-新增弹框数据
@bp.get('/add')
@authorize("system:size:add", log=True)
def add():
    return render_template('system/factory/size_management/add.html')


# 新增尺码-保存数据接口
@bp.post('/save')
@authorize("system:size:add", log=True)
def save():
    req = request.get_json(force=True)
    # 验证是否登录
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    # 获取当前登录用户的部门/工厂id
    dept_id = current_user.dept_id
    size = str_escape(req.get('size'))
    description = str_escape(req.get('description'))
    if not size:
        return fail_api(msg="型号或尺码名称不能为空")

    new_size = ProductModel(
        size=size,
        description=description,
        dept_id=dept_id
    )
    try:
        size = db.session.query(ProductModel).filter(
            ProductModel.size == size,
            ProductModel.dept_id == dept_id,
            ProductModel.is_deleted == 0
        ).first()
        if size:
            return fail_api(msg="该型号尺码已存在")
        db.session.add(new_size)
        db.session.commit()
        return success_api(msg="颜色成功")
    except Exception as e:
        db.session.rollback()
        return fail_api(msg="保存失败： " + str(e))


#  删除尺码-删除接口
@bp.delete('/remove/<int:id>')
@authorize("system:size:remove", log=True)
def delete(id):
    product_model = ProductModel.query.get(id)
    if product_model is None:
        return fail_api(msg="未找到颜色信息")
    product_model.is_deleted = True
    db.session.commit()
    if product_model.is_deleted:
        return success_api(msg="删除成功")
    else:
        return fail_api(msg="删除失败")


#  修改尺码-修改弹框数据
@bp.get('/edit/<int:size_id>')
@authorize("system:size:edit", log=True)
def edit(size_id):
    product_model = ProductModel.query.get(size_id)
    return render_template('system/factory/size_management/edit.html', product_model=product_model)


#  修改尺码-修改数据接口
@bp.put('/update')
@authorize("system:size:edit", log=True)
def update():
    req_json = request.get_json(force=True)
    product_model_data = {}
    product_model_id = str_escape(req_json.get("id"))
    size = str_escape(req_json.get("size"))
    description = str_escape(req_json.get('description'))
    if not size:
        return fail_api(msg="型号或尺码名称不能为空")
    product_model_data["size"] = size
    product_model_data["description"] = description
    try:
        product_model = ProductModel.query.get(product_model_id)
        if not product_model:
            return fail_api(msg="该型号尺码不存在")
        ProductModel.query.filter_by(id=product_model_id).update(product_model_data)
        db.session.commit()
        return success_api(msg="更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
