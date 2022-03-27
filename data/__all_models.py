import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class UsersParams(SqlAlchemyBase):
    __tablename__ = 'player_parameters'
    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    parameters = sqlalchemy.Column(sqlalchemy.JSON)


class Users(SqlAlchemyBase):
    __tablename__ = "users"

    login = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    password = sqlalchemy.Column(sqlalchemy.String)
    key_code_password = sqlalchemy.Column(sqlalchemy.String)
    ip = sqlalchemy.Column(sqlalchemy.String)
    lang = sqlalchemy.Column(sqlalchemy.String, default="EN")
    email = sqlalchemy.Column(sqlalchemy.String)

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

    # Тут находятся все свойства предмета в формате JSON
    """
    def (defence) - число. Базовая защита
    weight - число. Вес снаряжения
    ms (move speed) - число. Скорость действий с экипированным оружием
    """
    stats = sqlalchemy.Column(sqlalchemy.JSON)


class Melee(SqlAlchemyBase):
    __tablename__ = "melee"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    # [blade, knife, katana, light_saber]
    # [лезвие (меч), нож, катана, световой меч (пасхалка)]
    melee_type = sqlalchemy.Column(sqlalchemy.String)

    description = sqlalchemy.Column(sqlalchemy.String)


    # Тут находятся все свойства предмета в формате JSON
    """
    dmg - число. Базовый урон
    hc (hit chance) - число [0; 100]. Базовые шансы попасть в противника
    as (attack speed) - число. Базовая скорость атаки
    ms (move speed) - число. Скорость действий с экипированным оружием
    """
    stats = sqlalchemy.Column(sqlalchemy.JSON)


class Range(SqlAlchemyBase):
    __tablename__ = "range"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    # [bullet, laser]
    # Стреляющие: [пулями, лазерами]
    range_type = sqlalchemy.Column(sqlalchemy.String)

    description = sqlalchemy.Column(sqlalchemy.String)


    # Тут находятся все свойства предмета в формате JSON
    """
    dmg - число. Базовый урон
    hc (hit chance) - число [0; 100]. Базовые шансы попасть в противника
    as (attack speed) - число. Скорострельность
    mb (magazine bullets) - число. Кол-во патронов в магазине
    ms (move speed) - число. Скорость действий с экипированным оружием
    """
    stats = sqlalchemy.Column(sqlalchemy.JSON)


class ItemHealth(SqlAlchemyBase):
    __tablename__ = "item_health"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    description = sqlalchemy.Column(sqlalchemy.String)


    # Тут находятся все свойства предмета в формате JSON
    """
    ra (regeneration amount) - число. Те единицы здоровья, которые восстановит аптечка 
    """
    stats = sqlalchemy.Column(sqlalchemy.JSON)