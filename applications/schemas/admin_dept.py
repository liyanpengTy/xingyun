from flask_marshmallow.sqla import SQLAlchemyAutoSchema

from applications.models import Dept


class DeptSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Dept
        load_instance = True
        include_fk = True
        include_relationships = True