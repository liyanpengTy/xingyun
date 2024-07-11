import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from applications.extensions import db


class User(db.Model, UserMixin):
    __tablename__ = 'admin_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(20), nullable=False, comment='用户名')
    realname = db.Column(db.String(20), comment='真实名字')
    password_hash = db.Column(db.String(128), nullable=False, comment='哈希密码')
    phone = db.Column(db.String(20), comment='联系电话')
    user_type = db.Column(db.String(50), comment='用户类型')
    avatar = db.Column(db.String(255), comment='头像', default="/static/system/admin/images/avatar.jpg")
    remark = db.Column(db.String(255), comment='备注')
    enable = db.Column(db.Integer, default=0, comment='启用')
    dept_id = db.Column(db.Integer, comment='部门id')
    role_id = db.Column(db.Integer, comment='角色id')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否删除')
    start_time = db.Column(db.DateTime, default=None, comment='用户账户生效时间，可以为空')
    end_time = db.Column(db.DateTime, default=None, comment='用户账户结束时间，可以为空')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间')
    update_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment='更新时间')
    role = db.relationship('Role', secondary="admin_user_role", backref=db.backref('user'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)
