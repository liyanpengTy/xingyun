# -*- coding: utf-8 -*-
# @Time    : 2024/7/5 18:50
# @File    : cutting_bed_detail.py
# @Software: PyCharm
# @Author  : Roc

from applications.common.utils.http import fail_api, table_api, success_api
from applications.common.utils.rights import authorize
from applications.extensions import db
from applications.models import FactoryCuttingBedDetails, FactoryStaff, Role, FactoryCuttingBed, FactoryOrder, Color, ProductModel
from applications.schemas import FactoryCuttingBedDetailsSchema
from flask import Blueprint, render_template, request
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('cutting_bed_detail', __name__, url_prefix='/factory/cutting_bed_management/detail/')


# 裁床单详情-(派发、交货)
@bp.get('/no/<int:cutting_id>')
@authorize("system:cutting_bed:detail:main")
def main_no(cutting_id):
    return render_template('system/factory/cutting_bed_management/detail/no/main.html', cutting_id=cutting_id)


# 裁床单详情-（新增、修改）列表数据
@bp.get('/yes/<int:cutting_id>')
@authorize("system:cutting_bed:detail:main")
def main_yse(cutting_id):
    return render_template('system/factory/cutting_bed_management/detail/yes/main.html', cutting_id=cutting_id)


# 裁床单详情-列表数据
@bp.get('/data/<int:cutting_id>')
@authorize("system:cutting_bed:detail:main", log=True)
def data(cutting_id):
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    cutting_data = db.session.query(FactoryCuttingBedDetails).filter(
        FactoryCuttingBedDetails.cutting_bed_id == cutting_id
    ).layui_paginate()
    db.session.close()
    schema = FactoryCuttingBedDetailsSchema(many=True)
    result = schema.dump(cutting_data)
    return table_api(data=result, count=cutting_data.total)


# 裁床单详情-派发-弹框数据
@bp.get('/no/dispatch/<int:detail_id>')
@authorize("system:cutting_bed:detail:dispatch")
def dispatch(detail_id):
    dept_id = current_user.dept_id
    role_id = db.session.query(Role.id).filter(Role.name == '车位').scalar()
    staffs = db.session.query(FactoryStaff).filter(
        FactoryStaff.dept_id == dept_id,
        FactoryStaff.role_id == role_id,
        FactoryStaff.staff_status == 'active'
    ).all()
    db.session.close()
    return render_template('system/factory/cutting_bed_management/detail/no/dispatch.html', detail_id=detail_id, staffs=staffs)


# 裁床单详情-派发-保存数据
@bp.put('/no/dispatch_update')
@authorize("system:cutting_bed:detail:dispatch", log=True)
def dispatch_update():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")
    req = request.get_json(force=True)
    detail_id = req.get('detailId')
    staff_id = req.get('staffId')
    if not staff_id:
        return fail_api(msg="请选择工人")
    try:
        detail_db = db.session.query(FactoryCuttingBedDetails)
        details = detail_db.get(detail_id)
        if not details:
            return fail_api(msg="该详情单不存在")
        cutting_bed_id = details.cutting_bed_id
        cutting_bed = db.session.query(FactoryCuttingBed).get(cutting_bed_id)
        if not cutting_bed:
            return fail_api(msg="该裁床单不存在")
        orders = db.session.query(FactoryOrder).get(cutting_bed.order_id)
        if not orders:
            return fail_api(msg="该订单不存在")
        # 判断orders的staff_unit_price是否为空
        if not orders.staff_unit_price:
            return fail_api(msg="请联系厂长核实订单，确认是否自制还是外发")
        detail_db.filter_by(id=detail_id).update({
            'staff_id': staff_id,
            'dispatch_date': db.func.current_timestamp()
        })
        db.session.commit()
        return success_api(msg="派发成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="派发失败")
    finally:
        db.session.close()


# 裁床单详情-交货-弹框数据
@bp.get('/no/delivery/<int:detail_id>')
@authorize("system:cutting_bed:detail:delivery")
def delivery(detail_id):
    cutting_detail = db.session.query(FactoryCuttingBedDetails).get(detail_id)
    db.session.close()
    return render_template(
        'system/factory/cutting_bed_management/detail/no/delivery.html',
        detail_id=detail_id,
        cutting_detail=cutting_detail
    )


# 裁床单详情-交货-保存数据
@bp.put('/no/delivery_update')
@authorize("system:cutting_bed:detail:delivery", log=True)
def delivery_update():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")
    req = request.get_json(force=True)
    detail_id = req.get('detailId')
    staff_shipment_number = req.get('staffShipmentNumber')
    if not staff_shipment_number:
        return fail_api(msg="请输入交货数量")
    try:
        detail_db = db.session.query(FactoryCuttingBedDetails)
        details = detail_db.get(detail_id)
        if not details:
            return fail_api(msg="该详情单不存在")
        if not details.staff_id:
            return fail_api(msg="请先派发裁片给工人")
        detail_db.filter_by(id=detail_id).update({
            'staff_shipment_number': staff_shipment_number,
            'delivery_date': db.func.current_timestamp()
        })
        # 查询FactoryCuttingBedDetails表中相同的cutting_bed_id，查看其它未交货的详情单是否全部交货
        cutting_bed_id = details.cutting_bed_id
        cutting_details = db.session.query(FactoryCuttingBedDetails).filter(
            FactoryCuttingBedDetails.cutting_bed_id == cutting_bed_id,
            FactoryCuttingBedDetails.id != detail_id,
        ).all()
        # 遍历cutting_details,查看staff_shipment_number是否都不为空
        all_delivery = True
        for detail in cutting_details:
            if not detail.staff_shipment_number:
                all_delivery = False
                break
        # 如果所有详情单都交货，则更新cutting_bed表的status为'completed'
        if all_delivery:
            cutting_bed = db.session.query(FactoryCuttingBed).get(cutting_bed_id)
            db.session.query(FactoryOrder).filter(
                FactoryOrder.id == cutting_bed.order_id
            ).update({
                'order_status': 'Packing'
            })
        db.session.commit()
        return success_api(msg="交货成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="交货失败")
    finally:
        db.session.close()


# 裁床单详情-新增-弹框数据
@bp.get('/yes/add/<int:cutting_id>')
@authorize("system:cutting_bed:detail:add", log=True)
def add(cutting_id):
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
        'system/factory/cutting_bed_management/detail/yes/add.html',
        cutting_id=cutting_id,
        colors=colors,
        product_models=product_models
    )


# 裁床单详情-新增-保存数据
@bp.post('/yes/save')
@authorize("system:cutting_bed:detail:add", log=True)
def save():
    if not current_user.is_authenticated:
        return fail_api(msg="用户未登录")

    req = request.get_json(force=True)

    # 提取数据
    cutting_id = req.get('id')
    new_bundle_code = req.get('bundleCode')
    color_id = req.get('colorId')
    product_model_id = req.get('productModelId')
    quantity = req.get('quantity')

    # 验证数据
    if not new_bundle_code:
        return fail_api(msg="扎号不能为空")
    if not color_id:
        return fail_api(msg="颜色不能为空")
    if not quantity:
        return fail_api(msg="数量不能为空")

    # 获取默认尺码：均码。用户未选择尺码且该工厂无均码，则直接为空
    dept_id = current_user.dept_id
    if not product_model_id:
        product_model_id = db.session.query(ProductModel).filter(
            ProductModel.dept_id == dept_id,
            ProductModel.size == "均码",
            ProductModel.is_deleted == 0
        )

    new_detail_data = FactoryCuttingBedDetails(
        cutting_bed_id=cutting_id,
        bundle_code=new_bundle_code,
        color_id=color_id,
        product_model_id=product_model_id,
        quantity=quantity
    )

    # 每增新增一次数量，就往factory_order表的order_client_number字段增加值
    units_number = db.session.query(FactoryCuttingBed).filter(
        FactoryCuttingBed.id == cutting_id,
    ).with_entities(FactoryCuttingBed.units_number).scalar()
    if not units_number:
        units_number = quantity
    else:
        units_number += int(quantity)

    bundle_code_number = db.session.query(FactoryCuttingBed).filter(
        FactoryCuttingBed.id == cutting_id
    ).with_entities(FactoryCuttingBed.bundle_code_number).scalar()
    if not bundle_code_number:
        bundle_code_number = 1
    else:
        bundle_code_number += 1

    cutting_data = {
        "units_number": units_number,
        "bundle_code_number": bundle_code_number
    }

    try:
        # 查询工厂裁床明细单，new_bundle_code是否已存在。
        # cutting_bed_id, bundle_code唯一索引
        exist_detail = db.session.query(FactoryCuttingBedDetails).filter(
            FactoryCuttingBedDetails.cutting_bed_id == cutting_id,
            FactoryCuttingBedDetails.bundle_code == new_bundle_code
        ).first()
        if exist_detail:
            return fail_api(msg="该扎号已存在")
        db.session.add(new_detail_data)
        db.session.query(FactoryCuttingBed).filter_by(id=cutting_id).update(cutting_data)
        db.session.commit()
        return success_api(msg="新增裁床明细单成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="保存失败")
    finally:
        db.session.close()


# 裁床单详情-修改-弹框数据
@bp.get('/yes/edit/<int:detail_id>')
@authorize("system:cutting_bed:detail:edit", log=True)
def edit(detail_id):
    details = FactoryCuttingBedDetails.query.get(detail_id)
    product_model_id = details.product_model_id
    color_id = details.color_id

    dept_id = current_user.dept_id

    product_models = db.session.query(ProductModel).filter(
        ProductModel.dept_id == dept_id,
        ProductModel.is_deleted == 0
    ).all()

    colors = db.session.query(Color).filter(
        Color.dept_id == dept_id,
        Color.is_deleted == 0
    ).all()
    db.session.close()
    return render_template(
        'system/factory/cutting_bed_management/detail/yes/edit.html', details=details,
        product_model_id=product_model_id, color_id=color_id,
        product_models=product_models, colors=colors
    )


# 裁床单详情-修改-保存数据
@bp.put('/yes/update')
@authorize("system:cutting_bed:detail:edit", log=True)
def update():
    req = request.get_json(force=True)
    detail_data = {}
    cutting_id = req.get('cuttingId')
    detail_id = req.get('detailId')
    color_id = req.get('colorId')
    product_model_id = req.get('productModelId')
    new_quantity = req.get('quantity')

    # 验证数据
    if not color_id:
        return fail_api(msg="颜色不能为空")
    if not new_quantity:
        return fail_api(msg="数量不能为空")

    detail_data['color_id'] = color_id
    detail_data['product_model_id'] = product_model_id
    detail_data['quantity'] = new_quantity

    details = db.session.query(FactoryCuttingBedDetails).get(detail_id)
    quantity = details.quantity
    cuttings = db.session.query(FactoryCuttingBed).get(cutting_id)
    if not cuttings:
        return fail_api(msg=f"{cuttings.bed_number}号裁床单不存在")
    units_number = cuttings.units_number
    if new_quantity == quantity:
        new_cutting_units_number = int(units_number)
    else:
        new_cutting_units_number = int(units_number) - int(quantity) + int(new_quantity)
    cutting_data = {
        "units_number": new_cutting_units_number
    }

    try:
        FactoryCuttingBedDetails.query.filter_by(id=detail_id).update(detail_data)
        FactoryCuttingBed.query.filter_by(id=cutting_id).update(cutting_data)
        db.session.commit()
        return success_api(msg="修改裁床明细单成功")
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg="修改失败")
    finally:
        db.session.close()