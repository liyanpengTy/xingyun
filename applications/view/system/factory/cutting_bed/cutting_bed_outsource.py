# -*- coding: utf-8 -*-
# @Time    : 2024/7/5 23:45
# @File    : cutting_bed_outsource.py
# @Software: PyCharm
# @Author  : Roc
from applications.common.utils.http import fail_api, success_api, table_api
from applications.common.utils.rights import authorize
from applications.extensions import db
from applications.models import FactoryOutsource, FactoryOrder, FactoryCuttingBed, FactoryClient
from applications.schemas import FactoryOutsourceSchema
from flask import Blueprint, render_template, request
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('cutting_bed_outsource', __name__, url_prefix='/factory/cutting_bed_management/outsource')


# 工厂外协助管理
@bp.get('/<int:order_id>')
@authorize("system:outsource:main")
def main(order_id):
    return render_template('system/factory/cutting_bed_management/outsource/main.html', order_id=order_id)


@bp.get('/data/<int:order_id>')
@authorize("system:outsource:main")
def data(order_id):
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    query = db.session.query(FactoryOutsource).filter_by(order_id=order_id, is_delete=False).layui_paginate()
    db.session.commit()
    schema = FactoryOutsourceSchema(many=True)
    result = schema.dump(query)
    return table_api(data=result, count=query.total)


@bp.get('/add/<int:order_id>')
@authorize("system:cutting_bed:outsource:add")
def add(order_id):
    # 根据order_id获取订单的款号（product_model_number）
    product_model_number = db.session.query(FactoryOrder).filter_by(id=order_id).first().product_model_number
    units_number = db.session.query(FactoryCuttingBed).filter_by(order_id=order_id).first().units_number
    clients = db.session.query(FactoryClient).filter_by(
        dept_id=current_user.dept_id,
        is_deleted=False,
        client_type='partnerClient'
    ).all()
    db.session.commit()
    return render_template(
        'system/factory/cutting_bed_management/outsource/add.html',
        order_id=order_id,
        product_model_number=product_model_number,
        units_number=units_number,
        clients=clients,
    )


@bp.post('/save')
@authorize("system:cutting_bed:outsource:add")
def save():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req = request.get_json(force=True)
    order_id = req.get('orderId')
    units_number = req.get('unitsNumber')
    outsource_type = req.get('outsourceType')
    unit_price = req.get('unitPrice')
    client_id = req.get('clientId')

    if not outsource_type:
        return fail_api(msg='请输入协助类型')

    if not unit_price:
        return fail_api(msg='请输入单价')

    if not client_id:
        return fail_api(msg='请选择客户')

    # 保存工厂外协助信息
    factory_outsource = FactoryOutsource(
        order_id=order_id,
        client_id=client_id,
        outsource_type=outsource_type,
        unit_price=unit_price,
        quantity=units_number,
    )
    try:
        db.session.add(factory_outsource)
        db.session.commit()
        return success_api(msg='工厂外协助信息保存成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='工厂外协助信息保存失败')


@bp.get('/edit/<int:outsource_id>')
@authorize("system:cutting_bed:outsource:edit")
def edit(outsource_id):
    outsources = db.session.query(FactoryOutsource).get(outsource_id)
    product_model_number = db.session.query(FactoryOrder).filter_by(id=outsources.order_id).first().product_model_number
    units_number = db.session.query(FactoryCuttingBed).filter_by(order_id=outsources.order_id).first().units_number
    clients = db.session.query(FactoryClient).filter_by(
        dept_id=current_user.dept_id,
        is_deleted=False,
        client_type='partnerClient'
    ).all()
    return render_template(
        'system/factory/cutting_bed_management/outsource/edit.html',
        outsource_id=outsource_id,
        outsources=outsources,
        clients=clients,
        product_model_number=product_model_number,
        units_number=units_number,
    )


@bp.post('/update')
@authorize("system:cutting_bed:outsource:edit")
def update():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req = request.get_json(force=True)
    outsource_id = req.get('outsourceId')
    outsource_type = req.get('outsourceType')
    unit_price = req.get('unitPrice')
    client_id = req.get('clientId')

    if not outsource_type:
        return fail_api(msg='请输入协助类型')

    if not unit_price:
        return fail_api(msg='请输入单价')

    if not client_id:
        return fail_api(msg='请选择客户')

    factory_outsource = db.session.query(FactoryOutsource).get(outsource_id)
    if not factory_outsource:
        return fail_api(msg='ID为{}的协助信息不存在'.format(outsource_id))
    try:
        factory_outsource.outsource_type = outsource_type
        factory_outsource.unit_price = unit_price
        factory_outsource.client_id = client_id
        db.session.commit()
        return success_api(msg='协助信息更新成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='协助信息更新失败')


@bp.delete('/remove/<int:outsource_id>')
@authorize("system:cutting_bed:outsource:remove")
def remove(outsource_id):
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    factory_outsource = db.session.query(FactoryOutsource).get(outsource_id)
    if not factory_outsource:
        return fail_api(msg='ID为{}的工厂外协助信息不存在'.format(outsource_id))
    try:
        factory_outsource.is_delete = True
        db.session.commit()
        return success_api(msg='工厂协助信息删除成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='工厂协助信息删除失败')