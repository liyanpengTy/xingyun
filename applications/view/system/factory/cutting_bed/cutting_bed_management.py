# -*- coding: utf-8 -*-
# @Time    : 2024/7/5 1:38
# @File    : cutting_bed_management.py
# @Software: PyCharm
# @Author  : Roc

from flask import Blueprint, render_template, request
from applications.common.utils.http import table_api, fail_api, success_api
from applications.common.utils.rights import authorize
from applications.common.utils.validate import str_escape
from applications.models import FactoryCuttingBed, FactoryOrder, Dept, FactoryStaff, Role
from applications.schemas import FactoryCuttingBedSchema
from applications.extensions import db
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('cutting_bed_management', __name__, url_prefix='/factory/cutting_bed_management')


# 裁床管理-主页
@bp.get('/')
@authorize("system:cutting_bed:main")
def main():
    """ 传递页面数据 """
    return render_template('system/factory/cutting_bed_management/main.html')


# 裁床管理-列表数据
@bp.get('/data')
@authorize('system:cutting_bed:main')
def data():
    """ 查询接口 """
    if not current_user.is_authenticated:
        return table_api(msg='用户未登录')

    # 获取请求参数
    product_model_number = str_escape(request.args.get('productModelNumber', type=str))
    order_status = str_escape(request.args.get('orderStatus', type=str))
    start_date = str_escape(request.args.get('startDate', type=str))
    end_date = str_escape(request.args.get('endDate', type=str))

    user_dept_id = current_user.dept_id

    query_order = db.session.query(FactoryOrder).filter(
        FactoryOrder.dept_id == user_dept_id,
        FactoryOrder.is_deleted == 0
    ).all()

    if product_model_number:
        query_order = query_order.filter(FactoryOrder.product_model_number.contains(product_model_number))

    if order_status:
        query_order = query_order.filter(FactoryOrder.order_status == order_status)

    if start_date and not end_date:
        query_order = query_order.filter(FactoryOrder.cutting_date >= start_date)
    elif end_date and not start_date:
        query_order = query_order.filter(FactoryOrder.cutting_date <= end_date)
    elif start_date and end_date:
        query_order = query_order.filter(FactoryOrder.cutting_date >= start_date, FactoryOrder.cutting_date <= end_date)

    query_cutting_bed = db.session.query(FactoryCuttingBed).filter(
        FactoryCuttingBed.order_id.in_([order.id for order in query_order])
    ).layui_paginate()

    schema = FactoryCuttingBedSchema(many=True)
    result = schema.dump(query_cutting_bed)

    order_status_map = {
        "Submitted": "订单提交",
        "Cutting": "裁剪分包",
        "CuttingCompleted": "裁剪完成",
        "Sewing": "缝制生产",
        "Packing": "包装发货",
        "Completed": "完成订单",
    }
    for item in result:
        item['order_status'] = order_status_map.get(item['order_status'], item['order_status'])
    db.session.close()

    return table_api(data=result, count=query_cutting_bed.total)


# 裁床管理-新增弹框-弹框数据
@bp.get('/add')
@authorize('system:cutting_bed:add', log=True)
def add():
    """ 传递新增数据 """

    user_id = current_user.id
    role_id = db.session.query(Role.id).filter(Role.name == '裁床').scalar()
    dept_id = current_user.dept_id

    orders = db.session.query(FactoryOrder).filter(
        FactoryOrder.dept_id == dept_id,
        FactoryOrder.order_status == 'Cutting',
        FactoryOrder.is_deleted == 0
    ).all()

    staffs = db.session.query(FactoryStaff).filter(
        FactoryStaff.dept_id == dept_id,
        FactoryStaff.is_deleted == 0,
        FactoryStaff.role_id == role_id,
        FactoryStaff.enable == 1
    ).all()

    cutting_beds = db.session.query(FactoryCuttingBed).filter(
        FactoryCuttingBed.order_id.in_([order.id for order in orders]),
        FactoryCuttingBed.is_bed == 0
    ).all()

    db.session.close()

    return render_template(
        'system/factory/cutting_bed_management/add.html',
        orders=orders,
        staffs=staffs,
        cutting_beds=cutting_beds
    )


# 裁床管理-新增弹框-保存数据
@bp.post('/save')
@authorize('system:cutting_bed:add', log=True)
def save():
    """ 新增接口 """
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req = request.get_json(force=True)

    # 提取数据
    order_id = str_escape(req.get('orderId'))
    bed_number = str_escape(req.get('bedNumber'))
    staff_id = str_escape(req.get('staffId'))
    is_bed = str_escape(req.get('isBed'))
    parent_level_id = str_escape(req.get('parentLevelId'))
    parent_level_number = str_escape(req.get('parentLevelNumber'))

    # 校验数据
    if not order_id:
        return fail_api(msg='请选择订单')
    if not bed_number:
        return fail_api(msg='请输入床次')
    if not staff_id:
        return fail_api(msg='请选择裁货人员')

    new_cutting_bed = FactoryCuttingBed(
        bed_number=bed_number,
        order_id=order_id,
        staff_id=staff_id,
        is_bed=is_bed,
    )

    if is_bed == "1":
        if not parent_level_number:
            return fail_api(msg='请选择关联床次')
        new_cutting_bed.parent_level_id = parent_level_id
        new_cutting_bed.parent_level_number = parent_level_number

    try:
        cutting_bed = db.session.query(FactoryCuttingBed).filter(FactoryCuttingBed.order_id == order_id).all()
        bed_number = [bed.bed_number for bed in cutting_bed]
        if bed_number in bed_number:
            return fail_api(msg='该订单已存在该床次')
        db.session.add(new_cutting_bed)
        db.session.commit()
        return success_api(msg='新增成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='新增失败')
    finally:
        db.session.close()


# 裁床管理-修改弹框-弹框数据
@bp.get('/edit/<int:cutting_id>')
@authorize('system:cutting_bed:edit', log=True)
def edit(cutting_id):
    """ 传递修改数据 """

    cutting = FactoryCuttingBed.query.get(cutting_id)
    role_id = db.session.query(Role.id).filter(Role.name == '裁床').first()[0]
    dept_id = current_user.dept_id

    orders = db.session.query(FactoryOrder).filter(
        FactoryOrder.dept_id == dept_id,
        FactoryOrder.order_status == 'Cutting',
        FactoryOrder.is_deleted == 0
    ).all()

    staffs = db.session.query(FactoryStaff).filter(
        FactoryStaff.dept_id == dept_id,
        FactoryStaff.is_deleted == 0,
        FactoryStaff.role_id == role_id,
        FactoryStaff.enable == 1
    ).all()

    cutting_beds = db.session.query(FactoryCuttingBed).filter(
        FactoryCuttingBed.order_id.in_([order.id for order in orders]),
        FactoryCuttingBed.is_bed == 0,
        FactoryCuttingBed.id != cutting_id
    ).all()
    db.session.close()
    return render_template(
        'system/factory/cutting_bed_management/edit.html',
        cutting=cutting,
        orders=orders,
        staffs=staffs,
        cutting_beds=cutting_beds
    )

# 裁床管理-修改弹框-保存数据
@bp.post('/update')
@authorize('system:cutting_bed:edit', log=True)
def update():
    """ 修改接口 """
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req = request.get_json(force=True)

    # 提取数据
    cutting_id = str_escape(req.get('cuttingId'))
    order_id = str_escape(req.get('orderId'))
    new_bed_number = str_escape(req.get('bedNumber'))
    staff_id = str_escape(req.get('staffId'))
    is_bed = str_escape(req.get('isBed'))
    parent_level_id = str_escape(req.get('parentLevelId'))
    parent_level_number = str_escape(req.get('parentLevelNumber'))
    cutting_data = {}
    # 校验数据
    if not order_id:
        return fail_api(msg='请选择订单')
    cutting_data['order_id'] = order_id
    if not new_bed_number:
        return fail_api(msg='请输入床次')
    cutting_data['bed_number'] = new_bed_number
    if not staff_id:
        return fail_api(msg='请选择裁货人员')
    cutting_data['staff_id'] = staff_id
    # 判断是否有关联床次
    if is_bed == "1":
        if not parent_level_number:
            return fail_api(msg='请选择关联床次')
        cutting_data['is_bed'] = is_bed
        cutting_data['parent_level_id'] = parent_level_id
        cutting_data['parent_level_number'] = parent_level_number
    else:
        cutting_data['is_bed'] = is_bed
        cutting_data['parent_level_id'] = None
        cutting_data['parent_level_number'] = None

    # 保存数据
    try:
        cutting_db = db.session.query(FactoryCuttingBed)
        # 判断是否存在该裁床单
        cutting = cutting_db.get(cutting_id)
        if not cutting:
            return fail_api(msg='该裁床单不存在')
        # 判断是否存在该裁床单
        count_repeat = cutting_db.filter_by(order_id=order_id, bed_number=new_bed_number).count()
        if cutting.bed_number != new_bed_number:
            if count_repeat > 0:
                return fail_api(msg='该订单已存在该床次')
        # 判断是否有关联裁床单
        count_child = cutting_db.filter_by(parent_level_id=cutting_id).count()
        if cutting.bed_number != new_bed_number:
            if count_child > 0:
                return fail_api(msg='该裁床单有关联床次，请先取消关联床次后再修改床次')
        # 修改数据
        cutting_db.filter_by(id=cutting_id).update(cutting_data)
        db.session.commit()
        return success_api(msg='裁床单修改成功')
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='新增失败')
    finally:
        db.session.close()


# 裁床管理-完成裁剪，修改订单状态
@bp.post('/complete/<int:cutting_id>')
@authorize('system:cutting_bed:complete', log=True)
def complete(cutting_id):
    """ 完成裁剪分包状态，修改订单状态接口 """
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')
    try:
        # 获取裁床单信息
        cutting = db.session.query(FactoryCuttingBed).get(cutting_id)
        if not cutting:
            return fail_api(msg='该裁床单不存在')
        if cutting.is_completed is True:
            return fail_api(msg='该裁床单已完成')
        # 判断该裁床单是否有子级裁床单
        if cutting.is_bed == 0:
            # 获取关联裁床单信息
            relevance_cutting = db.session.query(FactoryCuttingBed).filter_by(parent_level_id=cutting_id).all()
            # 判断是否有关联裁床单
            if len(relevance_cutting) > 0:
                # 修改所有子级裁床单状态
                for cut in relevance_cutting:
                    db.session.query(FactoryCuttingBed).filter_by(id=cut.id).update({'is_completed': True})
            # 修改当前裁床单状态
            db.session.query(FactoryCuttingBed).filter_by(id=cutting_id).update({'is_completed': True})
        # 判断该裁床单是否有父级裁床单
        elif cutting.is_bed == 1:
            # 获取父级裁床单信息
            parent_level_cutting = db.session.query(FactoryCuttingBed).get(cutting.parent_level_id)
            # 获取该父级裁床单的关联裁床单信息
            relevance_cutting = db.session.query(FactoryCuttingBed).filter_by(parent_level_id=parent_level_cutting.id).all()
            # 判断是否有关联裁床单
            if len(relevance_cutting) > 0:
                # 修改所有子级裁床单状态
                for cut in relevance_cutting:
                    db.session.query(FactoryCuttingBed).filter_by(id=cut.id).update({'is_completed': True})
            # 修改父级裁床单状态
            db.session.query(FactoryCuttingBed).filter_by(id=parent_level_cutting.id).update({'is_completed': True})
        # 获取订单信息
        order = db.session.query(FactoryOrder).get(cutting.order_id)
        # 判断该订单的状态是否为”Cutting“,如果是，则修改订单状态为”CuttingCompleted“，并将FactoryOrder.cutting_date字段更新为当前时间
        if order.order_status == 'Cutting':
            db.session.query(FactoryOrder).filter_by(id=order.id).update({
                'order_status': 'CuttingCompleted',
                'cutting_date': db.func.current_timestamp()
            })
        else:
            return fail_api(msg='该订单id:{}的状态为{}数据异常，请联系管理员'.format(order.id, order.order_status))
        db.session.commit()
        return success_api(msg='“完成裁剪”操作成功，订单状态已更新')
    except Exception as e:
        db.session.rollback()
        return fail_api(msg='“完成裁剪”操作失败。{}'.format(e))
    finally:
        db.session.close()