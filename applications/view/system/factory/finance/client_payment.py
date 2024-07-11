# -*- coding: utf-8 -*-
# @Time    : 2024/7/8 20:36
# @File    : client_payment.py
# @Software: PyCharm
# @Author  : Roc
# 财务统计-客户回款/工厂付款

from flask import Blueprint, render_template, request
from applications.common.utils.rights import authorize
from applications.common.utils.http import table_api, fail_api, success_api
from flask_login import current_user
from applications.common.utils.validate import str_escape
from applications.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from applications.models import FactoryFinanceClient, FactoryOrder, FactoryFinanceClientDetail, FactoryOrderDetails, FactoryOutsource, FactoryClient
from applications.schemas import FactoryFinanceClientSchema
from applications.common.utils.get_date import get_date

bp = Blueprint('client_payment', __name__, url_prefix='/factory/finance_statistics/client_payment')


# 客户回款-主页
@bp.get('/')
@authorize("system:finance_statistics:client_payment:main")
def main():
    return render_template('system/factory/finance_statistics/client_payment/main.html')


def get_client_type_map():
    return {
        'orderClient': '订单客户',
        'externalClient': '外发客户',
        'partnerClient': '协作客户'
    }


# 客户回款-列表数据
@bp.get('/data')
@authorize("system:finance_statistics:client_payment:main")
def data():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    year_month = request.args.get('yearMonth', type=str)

    query = db.session.query(FactoryFinanceClient).filter(
        FactoryFinanceClient.dept_id == current_user.dept_id
    )

    if year_month:
        year = year_month[:4]
        month = year_month[5:]
        query = query.filter(
            FactoryFinanceClient.year == year,
            FactoryFinanceClient.month == month
        )

    query_finance_client = query.order_by(
        FactoryFinanceClient.year.desc(),
        FactoryFinanceClient.month.desc()
    ).layui_paginate()

    schema = FactoryFinanceClientSchema(many=True)
    result = schema.dump(query_finance_client)

    client_type_map = get_client_type_map()
    for item in result:
        item['client_type'] = client_type_map.get(item['client_type'], item['client_type'])
    db.session.close()
    return table_api(data=result, count=query_finance_client.total)


# 客户回款-生成回款数据
@bp.post('/save')
@authorize("system:finance_statistics:client_payment:add")
def save():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    year, month, start_date, end_date = get_date()
    dept_id = current_user.dept_id

    try:
        # 查询订单表，获取需要生成回款数据的订单数据
        orders = db.session.query(FactoryOrder).filter(
            FactoryOrder.dept_id == current_user.dept_id,
            FactoryOrder.order_status == "Completed",
            FactoryOrder.shipment_date >= start_date,
            FactoryOrder.shipment_date <= end_date,
            FactoryOrder.is_repayment == 0,
            FactoryOrder.is_deleted == 0
        ).all()
        if not orders:
            return fail_api(msg='没有需要生成回款数据的订单，请前往订单管理进行查看')

        # 遍历订单数据，生成回款数据
        for order in orders:
            """ 生成订单客户的回款数据 """
            order_id = order.id
            product_model_number = order.product_model_number
            order_client_id = order.order_client_id
            order_client_number = order.order_client_number
            order_client_unit_price = order.order_client_unit_price
            order_shipment_number = order.order_shipment_number
            shipment_date = order.shipment_date
            receivable_new = order_shipment_number * float(order_client_unit_price)
            staff_unit_price = order.staff_unit_price # 员工单价

            # 禁用自动刷新
            autoflush = db.session.autoflush
            db.session.autoflush = False

            try:
                finance_client_order = db.session.query(FactoryFinanceClient).filter(
                    FactoryFinanceClient.dept_id == dept_id,
                    FactoryFinanceClient.client_id == order_client_id,
                    FactoryFinanceClient.year == year,
                    FactoryFinanceClient.month == month
                ).first()

                # 计算应收款金额
                if finance_client_order:
                    receivable_old = finance_client_order.receivable
                    receivable = float(receivable_old) + float(receivable_new)
                    db.session.query(FactoryFinanceClient).filter_by(id=finance_client_order.id).update({
                        'receivable': receivable,
                        'balance': receivable
                    })
                else:
                    # 如果没有该客户的回款数据，则新增一条数据
                    new_finance_client = FactoryFinanceClient(
                        dept_id=current_user.dept_id,
                        client_id=order_client_id,
                        year=year,
                        month=month,
                        receivable=receivable_new,
                        balance=receivable_new
                    )
                    db.session.add(new_finance_client)
                    db.session.flush()

                finance_client_order = db.session.query(FactoryFinanceClient).filter(
                    FactoryFinanceClient.dept_id == current_user.dept_id,
                    FactoryFinanceClient.client_id == order_client_id,
                    FactoryFinanceClient.year == year,
                    FactoryFinanceClient.month == month
                ).first()

                # 新增回款数据明细
                new_finance_client_detail = FactoryFinanceClientDetail(
                    finance_client_id=finance_client_order.id,
                    date=shipment_date,
                    contract_no=product_model_number,
                    order_count=order_client_number,
                    order_shipment_number=order_shipment_number,
                    order_unit_price=order_client_unit_price,
                    amount=receivable_new
                )
                db.session.add(new_finance_client_detail)
                db.session.query(FactoryOrder).filter_by(id=order.id).update({'is_repayment': 1})

            finally:
                # 重新启用自动刷新
                db.session.autoflush = autoflush

            """ 生成外发客户的回款数据 """
            if not staff_unit_price:
                order_details = db.session.query(FactoryOrderDetails).filter_by(order_id=order_id).first()
                external_client_id = order_details.external_client_id
                external_client_number = order_details.external_client_number
                external_client_shipment_number = order_details.external_client_shipment_number
                external_client_unit_price = order_details.external_client_unit_price
                payable_new = external_client_shipment_number * float(external_client_unit_price)

                # 禁用自动刷新
                autoflush = db.session.autoflush
                db.session.autoflush = False

                try:
                    finance_client_external = db.session.query(FactoryFinanceClient).filter(
                        FactoryFinanceClient.dept_id == current_user.dept_id,
                        FactoryFinanceClient.client_id == external_client_id,
                        FactoryFinanceClient.year == year,
                        FactoryFinanceClient.month == month
                    ).first()

                    if finance_client_external:
                        payable_old = finance_client_external.payable
                        payable = float(payable_old) + float(payable_new)
                        db.session.query(FactoryFinanceClient).filter_by(id=finance_client_external.id).update({
                            'payable': payable,
                            'balance': payable
                        })
                    else:
                        new_finance_client = FactoryFinanceClient(
                            dept_id=current_user.dept_id,
                            client_id=external_client_id,
                            year=year,
                            month=month,
                            payable=payable_new,
                            balance=payable_new
                        )
                        db.session.add(new_finance_client)
                        db.session.flush()

                    finance_client_external = db.session.query(FactoryFinanceClient).filter(
                        FactoryFinanceClient.dept_id == current_user.dept_id,
                        FactoryFinanceClient.client_id == external_client_id,
                        FactoryFinanceClient.year == year,
                        FactoryFinanceClient.month == month
                    ).first()

                    new_finance_client_detail = FactoryFinanceClientDetail(
                        finance_client_id=finance_client_external.id,
                        date=shipment_date,
                        contract_no=product_model_number,
                        order_count=order_client_number,
                        order_shipment_number=order_shipment_number,
                        order_unit_price=order_client_unit_price,
                        external_number=external_client_number,
                        external_shipment_number=external_client_shipment_number,
                        external_unit_price=external_client_unit_price,
                        amount=payable_new
                    )
                    db.session.add(new_finance_client_detail)

                finally:
                    # 重新启用自动刷新
                    db.session.autoflush = autoflush

            """ 生成协助客户的回款数据 """
            outsources = db.session.query(FactoryOutsource).filter_by(order_id=order_id, is_delete=0).all()
            if not outsources:
                continue

            for outsource in outsources:
                outsource_client_id = outsource.client_id
                quantity = outsource.quantity
                unit_price = outsource.unit_price
                payable_new = quantity * float(unit_price)

                # 禁用自动刷新
                autoflush = db.session.autoflush
                db.session.autoflush = False

                try:
                    finance_client = db.session.query(FactoryFinanceClient).filter(
                        FactoryFinanceClient.dept_id == current_user.dept_id,
                        FactoryFinanceClient.client_id == outsource_client_id,
                        FactoryFinanceClient.year == year,
                        FactoryFinanceClient.month == month
                    ).first()

                    if finance_client:
                        payable_old = finance_client.payable
                        payable = float(payable_old) + float(payable_new)
                        db.session.query(FactoryFinanceClient).filter_by(id=finance_client.id).update({
                            'payable': payable,
                            'balance': payable
                        })
                    else:
                        # 如果没有该客户的回款数据，则新增一条数据
                        new_finance_client = FactoryFinanceClient(
                            dept_id=current_user.dept_id,
                            client_id=outsource_client_id,
                            year=year,
                            month=month,
                            payable=payable_new,
                            balance=payable_new
                        )
                        db.session.add(new_finance_client)
                        db.session.flush()

                    finance_client = db.session.query(FactoryFinanceClient).filter(
                        FactoryFinanceClient.dept_id == current_user.dept_id,
                        FactoryFinanceClient.client_id == outsource_client_id,
                        FactoryFinanceClient.year == year,
                        FactoryFinanceClient.month == month
                    ).first()

                    new_finance_client_detail = FactoryFinanceClientDetail(
                        finance_client_id=finance_client.id,
                        date=shipment_date,
                        contract_no=product_model_number,
                        order_count=order_client_number,
                        order_shipment_number=order_shipment_number,
                        order_unit_price=order_client_unit_price,
                        outsource_client_number=quantity,
                        outsource_unit_price=unit_price,
                        amount=payable_new
                    )
                    db.session.add(new_finance_client_detail)

                finally:
                    # 重新启用自动刷新
                    db.session.autoflush = autoflush

        db.session.commit()
        return success_api(msg='生成回款数据成功')
    except IntegrityError as e:
        db.session.rollback()
        return fail_api(msg='生成回款数据失败, 请检查数据后重试。错误信息：{}'.format(str(e)))
    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='生成回款数据失败, 请检查数据后重试。错误信息：{}'.format(str(e)))
    finally:
        db.session.close()



# 客户回款-修改（弹框数据）
@bp.get('/edit/<int:finance_client_id>')
@authorize("system:finance_statistics:client_payment:edit")
def edit(finance_client_id):
    finance_client = db.session.query(FactoryFinanceClient).get(finance_client_id)
    client = db.session.query(FactoryClient).get(finance_client.client_id)
    client_type_map = get_client_type_map()
    client.client_type = client_type_map.get(client.client_type, client.client_type)
    return render_template(
        'system/factory/finance_statistics/client_payment/edit.html',
        finance_client=finance_client,
        client=client
    )


# 客户回款-修改（保存数据）
@bp.put('/set_update')
@authorize("system:finance_statistics:client_payment:edit")
def set_update():
    if not current_user.is_authenticated:
        return fail_api(msg='用户未登录')

    req_json = request.get_json(force=True)
    received_get = str_escape(req_json.get("received"))
    paid_get = str_escape(req_json.get("paid"))
    client_type = req_json.get("clientType")
    client_id = req_json.get("clientId")

    if not received_get and not paid_get:
        return fail_api(msg='请输入收款金额或付款金额')

    try:
        finance_clients = db.session.query(FactoryFinanceClient).filter(
            FactoryFinanceClient.client_id == client_id,
            FactoryFinanceClient.is_settle == 0
        ).order_by(
            FactoryFinanceClient.year,
            FactoryFinanceClient.month
        ).all()

        if not finance_clients:
            return fail_api(msg='该客户没有任何回款数据')

        balance_sum = sum(finance_client.balance for finance_client in finance_clients)

        if client_type == '订单客户':
            if float(balance_sum) < float(received_get):
                return fail_api(
                    msg='收款金额【{}】大于当前回款数据中的所有未收款金额之和【{}】。请检查数据后重试'.format(received_get, balance_sum))
            update_finance_clients(finance_clients, received_get, 'received', 'receivable')

        elif client_type in ['外发客户', '协作客户']:
            if float(balance_sum) < float(paid_get):
                return fail_api(
                    msg='付款金额【{}】大于当前回款数据中的所有未付款金额之和【{}】。请检查数据后重试'.format(
                        paid_get, balance_sum))
            update_finance_clients(finance_clients, paid_get, 'paid', 'payable')

        else:
            return fail_api(msg='客户类型错误，请检查数据后重试')

        db.session.commit()
        return success_api(msg='设置回款数据成功')

    except SQLAlchemyError as e:
        db.session.rollback()
        return fail_api(msg='设置回款数据失败, 请检查数据后重试')
    finally:
        db.session.close()


def update_finance_clients(finance_clients, amount_get, field_name, target_field):
    """
    更新回款数据
    :param finance_clients: 回款数据列表
    :param amount_get: 收款金额或付款金额
    :param field_name: 字段名称，received或paid
    :param target_field: 目标字段名称，receivable或payable
    """
    amount_left = float(amount_get)
    for finance_client in finance_clients:
        balance_old = finance_client.balance
        if amount_left <= 0:
            break

        if amount_left >= balance_old:
            setattr(finance_client, field_name, getattr(finance_client, target_field))
            finance_client.balance = 0
            finance_client.is_settle = True
            amount_left -= float(balance_old)
        else:
            setattr(finance_client, field_name, amount_left)
            finance_client.balance = float(balance_old) - amount_left
            finance_client.is_settle = False
            amount_left = 0

        db.session.query(FactoryFinanceClient).filter_by(id=finance_client.id).update({
            field_name: getattr(finance_client, field_name),
            'balance': finance_client.balance,
            'is_settle': finance_client.is_settle
        })
