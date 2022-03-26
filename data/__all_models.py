import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class Users(SqlAlchemyBase):
    __tablename__ = "users"

    login = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    password = sqlalchemy.Column(sqlalchemy.String)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Commands(SqlAlchemyBase):
    __tablename__ = "commands"

    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    syntax = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    python_func = sqlalchemy.Column(sqlalchemy.String)


class Armor(SqlAlchemyBase):
    __tablename__ = "armor"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    # [head, torso, hands, legs, feet]
    # [голова, тело, ладони, ноги, ступни]
    slot = sqlalchemy.Column(sqlalchemy.String)

    description = sqlalchemy.Column(sqlalchemy.String)


class Melee(SqlAlchemyBase):
    __tablename__ = "melee"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    # [blade, knife, katana, light_saber]
    # [лезвие (меч), нож, катана, световой меч (пасхалка)]
    melee_type = sqlalchemy.Column(sqlalchemy.String)

    description = sqlalchemy.Column(sqlalchemy.String)