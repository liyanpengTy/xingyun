# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 23:50
# @File    : order_detail.py
# @Software: PyCharm
# @Author  : Roc
from datetime import datetime
from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import Dept, FactoryOrder, OrderItem, Color, ProductModel
from applications.schemas import OrderItemSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user
from sqlalchemy.orm import joinedload

bp = Blueprint('order_detail', __name__, url_prefix='/factory/order_management/detail')


# 订单详情页-不可修改（只读）；订单状态非“订单提交”
@bp.get('/no/<int:order_id>')
@authorize("system:order_detail:main")
def main_no(order_id):
    return render_template('system/factory/order_management/detail/no/main.html', order_id=order_id)


# 订单详情页-不可修改（只读）；订单状态非“订单提交”；获取订单详细信息
@bp.get('/no/data_no/<int:order_id>')
@authorize("system:order_detail:main")
def data_no(order_id):
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    order_items = OrderItem.query.filter(
        OrderItem.order_id == order_id
    ).layui_paginate()

    schema = OrderItemSchema(many=True)
    result = schema.dump(order_items)

    return table_api(data=result, count=order_items.total)


# 订单详情页-可修改；订单状态为“订单提交”
@bp.get('/yes/<int:order_id>')
@authorize("system:order_detail:main")
def main_yes(order_id):
    return render_template('system/factory/order_management/detail/yes/main.html', order_id=order_id)


# 订单详情页-可修改；订单状态为“订单提交”；获取订单详细信息
@bp.get('/yes/data_yes/<int:order_id>')
@authorize("system:order_detail:main")
def data_yes(order_id):
    # 检查用户认证状态
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    order_items = OrderItem.query.filter(
        OrderItem.order_id == order_id
    ).layui_paginate()

    # 使用Marshmallow序列化查询结果
    schema = OrderItemSchema(many=True)
    result = schema.dump(order_items)

    return table_api(data=result, count=order_items.total)


# 新增订单详细信息-弹框数据
@bp.get('/yes/add/<int:order_id>')
@authorize("system:order:detail:add", log=True)
def add(order_id):
    # 传递 订单id, 尺码id/名称, 颜色id/颜色
    dept_id = current_user.dept_id

    colors = db.session.query(Color).filter(
        Color.dept_id == dept_id,
        Color.is_deleted == 0
    ).all()

    product_models = db.session.query(ProductModel).filter(
        ProductModel.dept_id == dept_id,
        ProductModel.is_deleted == 0
    ).all()
    db.session.close()
    return render_template(
        'system/factory/order_management/detail/yes/add.html', order_id=order_id,
        colors=colors, product_models=product_models
    )

# 新增订单详细信息-保存订单详细信息
@bp.post('/yes/save')
@authorize("system:order:detail:add", log=True)
def save():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    req = request.get_json(force=True)

    # 提取数据
    order_id = req.get('id')
    color_id = req.get('colorId')
    product_model_id = req.get('productModelId')
    quantity = req.get('quantity')

    # 验证数据
    if not color_id:
        return fail_api(msg="颜色不能为空")
    if not quantity:
        return fail_api(msg="数量不能为空")

    # 获取默认尺码：均码。用户未选择尺码且该工厂无均码，则直接为空
    dept_id = current_user.dept_id
    if not product_model_id:
        product_model_id = ProductModel.query.filter(
            ProductModel.dept_id == dept_id,
            ProductModel.size == "均码",
            ProductModel.is_deleted == 0
        )

    new_item_data = OrderItem(
        order_id=order_id,
        color_id=color_id,
        product_model_id=product_model_id,
        quantity=quantity
    )

    # 每增新增一次数量，就往factory_order表的order_client_number字段增加值
    order_client_number = FactoryOrder.query.filter(
        FactoryOrder.id == order_id
    ).with_entities(FactoryOrder.order_client_number).scalar()
    if not order_client_number:
        order_client_number = quantity
    else:
        order_client_number += int(quantity)

    order_data = {"order_client_number": order_client_number}

    try:
        db.session.add(new_item_data)
        FactoryOrder.query.filter_by(id=order_id).update(order_data)
        db.session.commit()
        return success_api(msg="新增订单信息成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="保存失败")


# 修改订单详细信息-弹框数据
@bp.get('/yes/edit/<int:item_id>')
@authorize("system:order:detail:edit", log=True)
def edit(item_id):
    items = db.session.query(OrderItem).get(item_id)
    current_product_model_id = items.product_model_id
    current_color_id = items.color_id
    # 传递 订单id, 尺码id/名称, 颜色id/颜色
    dept_id = current_user.dept_id

    colors = db.session.query(Color).filter(
        Color.dept_id == dept_id,
        Color.is_deleted == 0
    ).all()

    product_models = db.session.query(ProductModel).filter(
        ProductModel.dept_id == dept_id,
        ProductModel.is_deleted == 0
    ).all()
    db.session.close()
    return render_template(
        'system/factory/order_management/detail/yes/edit.html', items=items, colors=colors, product_models=product_models,
        current_product_model_id=current_product_model_id, current_color_id=current_color_id
    )


# 修改订单详细信息-保存订单详细信息
@bp.put('/yes/update')
@authorize("system:order:detail:edit", log=True)
def update():
    req_json = request.get_json(force=True)
    item_data = {}
    order_id = str_escape(req_json.get("order_id"))
    item_id = str_escape(req_json.get("item_id"))
    color_id = str_escape(req_json.get("colorId"))
    product_model_id = str_escape(req_json.get("productModelId"))
    new_quantity = str_escape(req_json.get("quantity"))
    if not color_id:
        return fail_api(msg="颜色不能为空")
    if not new_quantity:
        return fail_api(msg="数量不能为空")

    item_data["color_id"] = color_id
    item_data["product_model_id"] = product_model_id
    item_data["quantity"] = new_quantity

    # 获取原来的 quantity 值,修改订单（FactoryOrder）中的 order_client_number 值
    items = OrderItem.query.get(item_id)
    quantity = items.quantity
    orders = FactoryOrder.query.get(order_id)
    if not orders:
        return fail_api(msg="订单不存在")
    order_client_number = orders.order_client_number
    if new_quantity == quantity:
        new_order_client_number = int(order_client_number)
    else:
        # 新的数量 != 原来的数量： 用订单总数量 - 原来的数量 + 新的数量
        # quantity 和 new_quantity 都是代表单个颜色、单个型号的数量。
        # order_client_number 代表该订单的总数量
        new_order_client_number = int(order_client_number) - int(quantity) + int(new_quantity)
    order_data = {"order_client_number": new_order_client_number}

    try:
        FactoryOrder.query.filter_by(id=order_id).update(order_data)
        OrderItem.query.filter_by(id=item_id).update(item_data)
        db.session.commit()
        return success_api(msg="订单信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
