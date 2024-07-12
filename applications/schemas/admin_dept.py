from flask_marshmallow.sqla import SQLAlchemyAutoSchema

from applications.models import Dept
from marshmallow import fields


class DeptSchema(SQLAlchemyAutoSchema):
    user_realname = fields.String(attribute='user.realname')

    class Meta:
        model = Dept
        load_instance = True
        include_fk = True
        include_relationships = True