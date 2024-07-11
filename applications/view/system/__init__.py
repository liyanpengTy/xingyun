from flask import Flask, Blueprint

from applications.view.system.dict import bp as dict_bp
from applications.view.system.file import bp as file_bp
from applications.view.system.index import bp as index_bp
from applications.view.system.log import bp as log_bp
from applications.view.system.mail import bp as mail_bp
from applications.view.system.monitor import bp as monitor_bp
from applications.view.system.passport import bp as passport_bp
from applications.view.system.power import bp as power_bp
from applications.view.system.rights import bp as right_bp
from applications.view.system.role import bp as role_bp
from applications.view.system.user import bp as user_bp
from applications.view.system.dept import bp as dept_bp
# 导入工厂模式下的蓝图
from .factory.order.order_management import bp as order_management_bp
from .factory.client.client_management import bp as client_management_bp
from .factory.staff.staff_management import bp as staff_management_bp
from .factory.color.color_management import bp as color_management_bp
from .factory.size.size_management import bp as size_management_bp
from .factory.order.order_edit import bp as order_edit_bp
from .factory.order.order_detail import bp as order_detail_bp
from .factory.cutting_bed.cutting_bed_management import bp as cutting_bed_management_bp
from .factory.cutting_bed.cutting_bed_detail import bp as cutting_bed_detail_bp
from .factory.cutting_bed.cutting_bed_outsource import bp as cutting_bed_outsource_bp
from .factory.finance.staff_wage import bp as staff_wage_bp
from .factory.finance.staff_wage_detail import bp as staff_wage_detail_bp
from .factory.finance.other_expenses import bp as other_expenses_bp
from .factory.finance.other_expenses_detail import bp as other_expenses_detail_bp
from .factory.finance.client_payment import bp as client_payment_bp
from .factory.finance.client_payment_detail import bp as client_payment_detail_bp
from .factory.finance.statistics import bp as statistics_bp
from .factory.finance.other_income_detail import bp as other_income_detail_bp
from .factory.finance.statistics_detail import bp as statistics_detail_bp


# 创建sys
system_bp = Blueprint('system', __name__, url_prefix='/system')


def register_system_bps(app: Flask):
    # 在admin_bp下注册子蓝图
    system_bp.register_blueprint(user_bp)
    system_bp.register_blueprint(file_bp)
    system_bp.register_blueprint(monitor_bp)
    system_bp.register_blueprint(log_bp)
    system_bp.register_blueprint(power_bp)
    system_bp.register_blueprint(role_bp)
    system_bp.register_blueprint(dict_bp)
    system_bp.register_blueprint(mail_bp)
    system_bp.register_blueprint(passport_bp)
    system_bp.register_blueprint(right_bp)
    system_bp.register_blueprint(dept_bp)

    # 注册工厂模式下的订单管理蓝图
    system_bp.register_blueprint(order_management_bp)
    # 注册工厂模式下的订单编辑蓝图
    system_bp.register_blueprint(order_edit_bp)
    # 注册工厂模式下的订单详情蓝图
    system_bp.register_blueprint(order_detail_bp)
    # 注册工厂模式下的客户管理蓝图
    system_bp.register_blueprint(client_management_bp)
    # 注册工厂模式下的员工管理蓝图
    system_bp.register_blueprint(staff_management_bp)
    # 注册工厂模式下的颜色管理蓝图
    system_bp.register_blueprint(color_management_bp)
    # 注册工厂模式下的尺码管理蓝图
    system_bp.register_blueprint(size_management_bp)
    # 注册工厂模式下的裁床管理蓝图
    system_bp.register_blueprint(cutting_bed_management_bp)
    # 注册工厂模式下的裁床详情蓝图
    system_bp.register_blueprint(cutting_bed_detail_bp)
    # 注册工厂模式下的厂外协作蓝图
    system_bp.register_blueprint(cutting_bed_outsource_bp)
    # 注册工厂模式下的财务统计中的员工工资蓝图
    system_bp.register_blueprint(staff_wage_bp)
    # 注册工厂模式下的财务统计中的员工工资详情蓝图
    system_bp.register_blueprint(staff_wage_detail_bp)
    # 注册工厂模式下的财务统计中的其他支出蓝图
    system_bp.register_blueprint(other_expenses_bp)
    # 注册工厂模式下的财务统计中的其他支出详情蓝图
    system_bp.register_blueprint(other_expenses_detail_bp)
    # 注册工厂模式下的财务统计中的客户回款/工厂付款蓝图
    system_bp.register_blueprint(client_payment_bp)
    # 注册工厂模式下的财务统计中的客户回款/工厂付款详情蓝图
    system_bp.register_blueprint(client_payment_detail_bp)
    # 注册工厂模式下的财务统计中的收支统计(其他收入详情)蓝图
    system_bp.register_blueprint(other_income_detail_bp)
    # 注册工厂模式下的财务统计中的收支统计蓝图
    system_bp.register_blueprint(statistics_bp)
    # 注册工厂模式下的财务统计中的收支统计-其他收入详情蓝图
    system_bp.register_blueprint(statistics_detail_bp)

    # 注册首页蓝图
    app.register_blueprint(index_bp)
    app.register_blueprint(system_bp)
