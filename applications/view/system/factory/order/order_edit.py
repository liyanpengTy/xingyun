# -*- coding: utf-8 -*-
# @Time    : 2024/7/4 23:18
# @File    : order_edit.py
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

bp = Blueprint('order_edit', __name__, url_prefix='/factory/order_management/edit')


# 修改订单-订单状态：订单提交-修改弹框数据
@bp.get('/edit_submitted/<int:order_id>')
@authorize("system:order:edit_Submitted", log=True)
def edit_submitted(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    clients = db.session.query(FactoryClient).filter(
        FactoryClient.is_deleted == 0
        and FactoryClient.dept_id == order.dept_id
    ).all()
    current_order_client_id = order.order_client_id
    current_delivery_date = order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else "1900-01-01"
    current_order_date = order.order_date.strftime('%Y-%m-%d') if order.order_date else "1900-01-01"
    db.session.close()
    return render_template(
        'system/factory/order_management/edit/submitted.html',
        order=order,
        clients=clients,
        current_order_client_id=current_order_client_id,
        current_delivery_date=current_delivery_date,
        current_order_date=current_order_date,
    )


# 修改订单-订单状态：订单提交-修改订单接口
@bp.put('/update_submitted')
@authorize("system:order:edit_Submitted", log=True)
def update_submitted():
    req_json = request.get_json(force=True)
    order_data = {}
    order_id = str_escape(req_json.get("id"))
    product_model_number = str_escape(req_json.get("ProductModelNumber"))
    order_client_id = str_escape(req_json.get("clientId"))
    order_client_unit_price = str_escape(req_json.get("orderClientUnitPrice"))
    order_date = str_escape(req_json.get("orderDate"))
    delivery_date = str_escape(req_json.get("deliveryDate"))

    if not product_model_number:
        return fail_api(msg="款号不能为空")
    if not order_client_id:
        return fail_api(msg="客户姓名不能为空")
    if not order_client_unit_price:
        return fail_api(msg="客户单价不能为空")

    order_data["product_model_number"] = product_model_number
    order_data["order_client_id"] = order_client_id
    order_data["order_client_unit_price"] = order_client_unit_price
    order_data["order_date"] = order_date if order_date else None
    order_data["delivery_date"] = delivery_date if delivery_date else None

    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        return success_api(msg="订单信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()


# 修改订单-订单状态：裁剪分包/裁剪完成-修改弹框数据
@bp.get('/edit_cutting/<int:order_id>')
@authorize("system:order:edit_Cutting", log=True)
def edit_cutting(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    current_client_names = db.session.query(FactoryClient).filter(
        FactoryClient.id == order.order_client_id
    ).all()
    current_client_name = current_client_names[0].client_name if current_client_names else ""
    current_delivery_date = order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else "1900-01-01"
    current_order_date = order.order_date.strftime('%Y-%m-%d') if order.order_date else "1900-01-01"
    db.session.close()
    return render_template(
        'system/factory/order_management/edit/cutting.html',
        order=order,
        current_delivery_date=current_delivery_date,
        current_order_date=current_order_date,
        current_client_name=current_client_name,
    )


# 修改订单-订单状态：裁剪分包/裁剪完成-修改订单接口
@bp.put('/update_edit_cutting')
@authorize("system:order:edit_Cutting", log=True)
def update_cutting():
    req_json = request.get_json(force=True)
    order_data = {}
    order_id = str_escape(req_json.get("id"))
    order_client_unit_price = str_escape(req_json.get("orderClientUnitPrice"))
    order_date = str_escape(req_json.get("orderDate"))
    delivery_date = str_escape(req_json.get("deliveryDate"))

    if not order_client_unit_price:
        return fail_api(msg="客户单价不能为空")

    order_data["order_client_unit_price"] = order_client_unit_price
    order_data["order_date"] = order_date if order_date else None
    order_data["delivery_date"] = delivery_date if delivery_date else None

    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        return success_api(msg="订单信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()


# 修改订单-订单状态：缝制生产，员工生产-修改弹框数据
@bp.get('/edit_sewing_staff/<int:order_id>')
@authorize("system:order:edit_Sewing_staff", log=True)
def edit_sewing_staff(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    current_client_names = db.session.query(FactoryClient).filter(
        FactoryClient.id == order.order_client_id
    ).all()
    current_client_name = current_client_names[0].client_name if current_client_names else ""
    current_delivery_date = order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else "1900-01-01"
    db.session.close()
    return render_template(
        'system/factory/order_management/edit/sewing_staff.html',
        order=order,
        current_delivery_date=current_delivery_date,
        current_client_name=current_client_name,
    )


# 修改订单-订单状态：缝制生产，员工生产-修改订单接口
@bp.put('/update_sewing_staff')
@authorize("system:order:edit_Sewing_staff", log=True)
def update_sewing_staff():
    req_json = request.get_json(force=True)
    order_data = {}
    order_id = str_escape(req_json.get("id"))
    order_client_unit_price = str_escape(req_json.get("orderClientUnitPrice"))
    staff_unit_price = str_escape(req_json.get("staffUnitPrice"))
    delivery_date = str_escape(req_json.get("deliveryDate"))

    if not order_client_unit_price:
        return fail_api(msg="客户单价不能为空")
    if not staff_unit_price:
        return fail_api(msg="员工单价不能为空")

    order_data["order_client_unit_price"] = order_client_unit_price
    order_data["staff_unit_price"] = staff_unit_price
    order_data["delivery_date"] = delivery_date if delivery_date else None

    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        return success_api(msg="订单信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()


# 修改订单-订单状态：缝制生产，外发客户生产-修改弹框数据
@bp.get('/edit_sewing_client/<int:order_id>')
@authorize("system:order:edit_Sewing_client", log=True)
def edit_sewing_client(order_id):
    order = db.session.query(FactoryOrder).get(order_id)
    current_client_names = db.session.query(FactoryClient).filter(
        FactoryClient.id == order.order_client_id
    ).all()
    details = db.session.query(FactoryOrderDetails).filter(
        FactoryOrderDetails.order_id == order.id
    ).all()
    sewing_client_names = db.session.query(FactoryClient).get(details[0].external_client_id) if details else None
    current_delivery_date = order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else "1900-01-01"
    db.session.close()
    return render_template(
        'system/factory/order_management/edit/sewing_client.html',
        order=order,
        details=details,
        current_client_names=current_client_names,
        current_delivery_date=current_delivery_date,
        sewing_client_names=sewing_client_names
    )


# 修改订单-订单状态：缝制生产，外发客户生产-修改订单接口
@bp.put('/update_sewing_client')
@authorize("system:order:edit_Sewing_client", log=True)
def update_sewing_client():
    req_json = request.get_json(force=True)
    order_data = {}
    details_data = {}
    order_id = str_escape(req_json.get("id"))
    details_id = str_escape(req_json.get("detailsId"))
    order_client_unit_price = str_escape(req_json.get("orderClientUnitPrice"))
    delivery_date = str_escape(req_json.get("deliveryDate"))
    external_client_number = str_escape(req_json.get("externalClientNumber"))
    external_client_unit_price = str_escape(req_json.get("externalClientUnitPrice"))

    if not order_client_unit_price:
        return fail_api(msg="客户单价不能为空")
    if not external_client_number:
        return fail_api(msg="外发数量不能为空")
    if not external_client_unit_price:
        return fail_api(msg="外发单价不能为空")

    order_data["order_client_unit_price"] = order_client_unit_price
    details_data["external_client_number"] = external_client_number
    details_data["external_client_unit_price"] = external_client_unit_price
    order_data["delivery_date"] = delivery_date if delivery_date else None

    try:
        order = db.session.query(FactoryOrder).get(order_id)
        if not order:
            return fail_api(msg="订单不存在")
        db.session.query(FactoryOrder).filter_by(id=order_id).update(order_data)
        details = db.session.query(FactoryOrderDetails).get(details_id)
        if not details:
            return fail_api(msg="订单详情不存在")
        db.session.query(FactoryOrderDetails).filter_by(id=details_id).update(details_data)
        db.session.commit()
        return success_api(msg="订单信息更新成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="更新失败" + str(e))
    finally:
        db.session.close()
