# -*- coding: utf-8 -*-
# @Time    : 2024/7/3 22:45
# @File    : order_management.py
# @Software: PyCharm
# @Author  : Roc

from datetime import datetime
from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.extensions import db
from applications.models import Role, Dept, FactoryClient, FactoryOrder, FactoryOrderDetails, OrderItem
from applications.schemas import FactoryOrderSchema, OrderItemSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user
from sqlalchemy.orm import joinedload

bp = Blueprint('order_management', __name__, url_prefix='/factory/order_management')

def get_param(param_name, param_type):
    """
    获取请求参数
    :param param_name: 参数名
    :param param_type: 参数类型
    :return: 参数值
    """
    return str_escape(request.args.get(param_name, type=param_type))


def get_order_status_map():
    """
    获取订单状态映射
    :return: 订单状态映射
    """
    return {
        "Submitted": "订单提交",
        "Cutting": "裁剪分包",
        "CuttingCompleted": "裁剪完成",
        "Sewing": "缝制生产",
        "Packing": "包装发货",
        "Completed": "完成订单",
    }


def get_is_repayment_map():
    """
    获取是否还款映射
    :return: 是否还款映射
    """
    return {
        0: "否",
        1: "是"
    }


# 订单管理
@bp.get('/')
@authorize("system:order:main")
def main():
    return render_template('system/factory/order_management/main.html')


# 订单管理-列表数据
@bp.get('/data')
@authorize("system:order:main")
def data():
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    client_name = get_param('clientName', str)
    product_model_number = get_param('ProductModelNumber', str)
    order_status = get_param('orderStatus', str)
    user_dept_id = current_user.dept_id

    query = db.session.query(FactoryOrder).filter(
        FactoryOrder.dept_id == user_dept_id,
        FactoryOrder.is_deleted != 1
    )

    if client_name:
        client_id = db.session.query(FactoryClient.id).filter(
            FactoryClient.client_name.contains(client_name),
            FactoryClient.dept_id == user_dept_id,
            FactoryClient.client_type == 'orderClient',
            FactoryClient.is_deleted == 0
        ).scalar()
        if client_id:
            query = query.filter(FactoryOrder.order_client_id == client_id)

    if product_model_number:
        query = query.filter(FactoryOrder.product_model_number.contains(product_model_number))

    if order_status:
        query = query.filter(FactoryOrder.order_status == order_status)

    query_result = query.options(
        joinedload(FactoryOrder.order_details)
    ).order_by(FactoryOrder.id.desc()).layui_paginate()

    schema = FactoryOrderSchema(many=True)
    result = schema.dump(query_result)

    order_status_map = get_order_status_map()
    is_repayment_map = get_is_repayment_map()

    for item in result:
        item['order_status'] = order_status_map.get(item['order_status'], item['order_status'])
        item['is_repayment'] = is_repayment_map.get(item['is_repayment'], item['is_repayment'])

    db.session.close()
    return table_api(data=result, count=query_result.total)


# 订单管理-新增弹框数据
@bp.get('/add')
@authorize("system:order:add", log=True)
def add():
    if current_user.is_authenticated:
        user_id = current_user.id
        dept_id = current_user.dept_id
        factory_clients = db.session.query(FactoryClient).filter(
            FactoryClient.dept_id == dept_id,
            FactoryClient.client_type == 'orderClient',
            FactoryClient.is_deleted == 0
        ).all() if dept_id else []
    else:
        factory_clients = []
    db.session.close()
    return render_template('system/factory/order_management/add.html', factory_clients=factory_clients)


# 订单管理-新增接口
@bp.post('/save')
@authorize("system:order:add", log=True)
def save():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    req = request.get_json(force=True)
    product_model_number = req.get('ProductModelNumber')
    order_client_unit_price = req.get('orderClientUnitPrice')
    order_date = req.get('orderDate')
    delivery_date = req.get('deliveryDate')
    order_client_id = req.get('clientId')

    if not product_model_number:
        return fail_api(msg="款号不能为空")
    if not order_client_id:
        return fail_api(msg="客户姓名不能为空")
    if not order_client_unit_price:
        return fail_api(msg="客户单价不能为空")

    order_user_id = current_user.id
    dept_id = current_user.dept_id

    new_order = FactoryOrder(
        product_model_number=product_model_number,
        order_client_unit_price=order_client_unit_price,
        order_date=order_date,
        delivery_date=delivery_date,
        order_client_id=order_client_id,
        order_user_id=order_user_id,
        dept_id=dept_id
    )

    try:
        db.session.add(new_order)
        db.session.commit()
        return success_api(msg="新增订单成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="保存失败")
    finally:
        db.session.close()


# 确认订单按钮-修改订单状态，进入裁剪分包阶段
@bp.post('/verify/<int:order_id>')
@authorize("system:order:verify", log=True)
def verify_order(order_id):
    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        order_data = {"order_status": "Cutting"}
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        return success_api(msg="确认订单成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败")
    finally:
        db.session.close()


# 订单管理-自制订单-弹框数据
@bp.get('/abstain/<int:order_id>')
@authorize("system:order:abstain", log=True)
def abstain(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    clients = db.session.query(FactoryClient).get(order.order_client_id)
    db.session.close()
    return render_template(
        'system/factory/order_management/abstain.html',
        order=order,
        clients=clients,
    )


# 订单管理-自制订单-保存信息，更新订单状态
@bp.put('/update_abstain')
@authorize("system:order:abstain", log=True)
def update_abstain():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    req = request.get_json(force=True)
    order_data = {}
    staff_unit_price = req.get('staffUnitPrice')
    order_id = req.get('id')

    if not staff_unit_price:
        return fail_api(msg="员工单价不能为空")

    order_data['staff_unit_price'] = staff_unit_price
    order_data['order_status'] = 'Sewing'

    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        return success_api(msg="已进入自制环节，更新订单状态")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()


# 订单管理-外发订单-弹框数据
@bp.get('/outsource/<int:order_id>')
@authorize("system:order:outsource", log=True)
def outsource(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    client_abstain = db.session.query(FactoryClient).get(order.order_client_id)
    client_outsources = db.session.query(FactoryClient).filter(
        FactoryClient.client_type == 'externalClient',
        FactoryClient.dept_id == order.dept_id
    )
    db.session.close()
    return render_template(
        'system/factory/order_management/outsource.html',
        order=order,
        client_abstain=client_abstain,
        client_outsources=client_outsources
    )


# 订单管理-外发订单-保存信息，更新订单状态
@bp.post('/save_outsource')
@authorize("system:order:outsource", log=True)
def save_outsource():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    req = request.get_json(force=True)
    order_data = {}
    order_id = req.get('id')
    external_client_id = req.get('clientId')
    external_client_number = req.get('externalClientNumber')
    external_client_unit_price = req.get('externalClientUnitPrice')

    if not external_client_id:
        return fail_api(msg="外发客户不能为空")
    if not external_client_number:
        return fail_api(msg="外发数量不能为空")
    if not external_client_unit_price:
        return fail_api(msg="外发单价不能为空")

    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        order_data['order_status'] = 'Sewing'
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        new_order_details = FactoryOrderDetails(
            order_id=order_id,
            external_client_id=external_client_id,
            external_client_number=external_client_number,
            external_client_unit_price=external_client_unit_price,
        )
        db.session.add(new_order_details)
        db.session.commit()
        return success_api(msg="已进入外发环节，更新订单状态")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()


# 订单管理-外发收货-弹框数据
@bp.get('/outsource_receive/<order_ids>')
@authorize("system:order:outsource_receive", log=True)
def outsource_receive(order_ids):
    order_ids = order_ids.split(',')
    orders = db.session.query(FactoryOrder).filter(
        FactoryOrder.id.in_(order_ids)
    ).all()
    order_ids = [int(order_id) for order_id in order_ids]
    delivery_data = {}
    number = 1
    for order in orders:
        order_details = db.session.query(FactoryOrderDetails).filter_by(order_id=order.id).first()
        client_name = db.session.query(FactoryClient).get(order_details.external_client_id).client_name
        undelivered_quantity = order_details.external_client_number - order_details.external_client_shipment_number if order_details.external_client_shipment_number else order_details.external_client_number
        delivery_data[number] = {
            "order_id": order.id,
            "product_model_number": order.product_model_number,
            "client_name": client_name,
            "external_client_number": order_details.external_client_number,
            "undelivered_quantity": undelivered_quantity,
            "delivery_date": order.delivery_date.strftime('%Y-%m-%d'),
        }
        number += 1
    db.session.close()
    return render_template(
        'system/factory/order_management/outsource_receive.html',
        delivery_data=delivery_data,
        order_ids_len=len(order_ids),
    )


# 订单管理-外发收货-保存信息，更新订单状态
@bp.put("/outsource_receive_update")
@authorize("system:order:outsource_receive", log=True)
def outsource_receive_update():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    order_details_data = {}
    req = request.get_json(force=True)
    order_ids_len = str_escape(req.get("orderIdsLen"))

    for i in range(int(order_ids_len)):
        order_id = str_escape(req.get("orderId_" + str(i + 1)))
        external_client_shipment_number_new = str_escape(req.get("externalClientShipmentNumber_" + str(i + 1)))
        order_details = db.session.query(FactoryOrderDetails).filter_by(order_id=order_id).first()
        if not external_client_shipment_number_new:
            return fail_api(msg="交货数量不能为空")
        if not order_details:
            return fail_api(msg="订单详情不存在")
        external_client_shipment_number_old = order_details.external_client_shipment_number if order_details.external_client_shipment_number else 0
        external_client_shipment_number = int(external_client_shipment_number_old) + int(external_client_shipment_number_new)
        order_details_data[i] = {
            "id": order_details.id,
            "external_client_shipment_number": external_client_shipment_number
        }

    try:
        for i in range(int(order_ids_len)):
            order_id = str_escape(req.get("orderId_" + str(i + 1)))
            order = db.session.query(FactoryOrder).get(order_id)
            if not order:
                return fail_api(msg="订单不存在")
            order_details = db.session.query(FactoryOrderDetails).get(order_details_data[i]["id"])
            if not order_details:
                return fail_api(msg="订单详情不存在")

            external_client_number = order_details.external_client_number
            external_client_shipment_number_old = order_details.external_client_shipment_number if order_details.external_client_shipment_number else 0
            external_client_shipment_number_new = order_details_data[i]["external_client_shipment_number"]

            if int(external_client_number) == int(external_client_shipment_number_old) + int(external_client_shipment_number_new):
                db.session.query(FactoryOrder).filter_by(id=order_id).update({"order_status": "Packing"})
            elif int(external_client_number) < int(external_client_shipment_number_old) + int(external_client_shipment_number_new):
                return fail_api(msg="外发客户交货的数量不能超过给外发客户的数量")
            db.session.query(FactoryOrderDetails).filter_by(id=order_details.id).update(order_details_data[i])

        db.session.commit()
        return success_api(msg="订单收货成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="收货失败" + str(e))
    finally:
        db.session.close()


# 订单管理-出货-弹框数据
@bp.get('/delivery/<order_ids>')
@authorize("system:order:delivery", log=True)
def delivery(order_ids):
    order_ids = order_ids.split(',')
    orders = db.session.query(FactoryOrder).filter(
        FactoryOrder.id.in_(order_ids)
    ).all()
    order_ids = [int(order_id) for order_id in order_ids]
    delivery_data = {}
    number = 1
    for order in orders:
        client_name = db.session.query(FactoryClient).get(order.order_client_id).client_name
        backlog_quantity = order.order_client_number - order.order_shipment_number if order.order_shipment_number else order.order_client_number
        delivery_data[number] = {
            "order_id": order.id,
            "product_model_number": order.product_model_number,
            "client_name": client_name,
            "order_client_number": order.order_client_number,
            "backlog_quantity": backlog_quantity,
            "delivery_date": order.delivery_date.strftime('%Y-%m-%d'),
        }
        number += 1
    db.session.close()
    return render_template(
        'system/factory/order_management/delivery.html',
        delivery_data=delivery_data,
        order_ids_len=len(order_ids),
    )


# 订单管理-出货-保存信息，更新订单状态
@bp.put("/delivery_update")
@authorize("system:order:delivery", log=True)
def delivery_update():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    order_data = {}
    req = request.get_json(force=True)
    order_ids_len = str_escape(req.get("orderIdsLen"))

    for i in range(int(order_ids_len)):
        order_id = str_escape(req.get("orderId_" + str(i + 1)))
        order_shipment_number_new = str_escape(req.get("orderShipmentNumber_" + str(i + 1)))
        if not order_shipment_number_new:
            return fail_api(msg="订单出货数量不能为空")
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        order_shipment_number_old = order.order_shipment_number if order.order_shipment_number else 0
        order_shipment_number = int(order_shipment_number_old) + int(order_shipment_number_new)
        order_data[i] = {
            "id": order_id,
            "order_shipment_number": order_shipment_number,
            "shipment_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    try:
        for i in range(int(order_ids_len)):
            order_id = order_data[i]["id"]
            order = db.session.query(FactoryOrder).get(order_id)
            if not order:
                return fail_api(msg="订单不存在")
            order_shipment_number_old = order.order_shipment_number if order.order_shipment_number else 0
            order_shipment_number_new = order_data[i]["order_shipment_number"]
            if int(order.order_client_number) <= int(order_shipment_number_old) + int(order_shipment_number_new):
                db.session.query(FactoryOrder).filter_by(id=order_id).update({"order_status": "Completed"})
            db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data[i])
        db.session.commit()
        return success_api(msg="订单出货成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="出货失败" + str(e))
    finally:
        db.session.close()


# 订单管理-删除
@bp.delete('/remove/<int:order_id>')
@authorize("system:order:remove", log=True)
def delete(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    if order is None:
        return fail_api(msg="未找到订单信息")
    try:
        order.is_deleted = True
        db.session.commit()
        return success_api(msg="删除成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="删除失败")
    finally:
        db.session.close()
