import json

import sqlalchemy
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


# ======== Users ========
class UsersParams(SqlAlchemyBase):
    __tablename__ = 'userParams'

    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    default_stats = {
        "lvl": 1,  # уровень
        "money": 100,  # деньги
        "hp": 100,  # базовое здоровье
        "energy": 5,  # базовое кол-во действий за ход
        "defence": 5,  # базовая защита
        "attack": 5,  # базовый урон в ближнем бою
        "acc": 5,  # базовая точность %. 0.05 при расчётах
    }
    stats = sqlalchemy.Column(sqlalchemy.JSON, default=json.dumps(default_stats))

    # [count, durability, table, itemName]
    default_items = {"items": [[1, "ItemMaterial", "ITEM_MATERIAL_DEBUG_NAME"]]}
    items = sqlalchemy.Column(sqlalchemy.JSON, default=json.dumps(default_items))


class Users(SqlAlchemyBase):
    __tablename__ = "users"

    login = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    password = sqlalchemy.Column(sqlalchemy.String)
    key_code_password = sqlalchemy.Column(sqlalchemy.String)
    lang = sqlalchemy.Column(sqlalchemy.String, default="EN")
    email = sqlalchemy.Column(sqlalchemy.String)
    friends = sqlalchemy.Column(sqlalchemy.String, default="[]")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)



# ======== Commands ========

class Commands(SqlAlchemyBase):
    __tablename__ = "commands"

    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    syntax = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    python_func = sqlalchemy.Column(sqlalchemy.String)



# ======== Inventory ========
class ItemMaterial(SqlAlchemyBase):
    __tablename__ = "itemMaterial"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)


class ItemHeal(SqlAlchemyBase):
    __tablename__ = "itemHeal"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    healAmount = sqlalchemy.Column(sqlalchemy.Integer)


class ItemArmor(SqlAlchemyBase):
    __tablename__ = "itemArmor"


    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)

    # [head, torso, hands, legs, feet]
    # [голова, тело, ладони, ноги, ступни]
    slot = sqlalchemy.Column(sqlalchemy.String)
    defence = sqlalchemy.Column(sqlalchemy.Integer)


class ItemMeleeWeapon(SqlAlchemyBase):
    __tablename__ = "itemMeleeWeapon"

    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)

    energyCost = sqlalchemy.Column(sqlalchemy.Integer)
    damage = sqlalchemy.Column(sqlalchemy.Integer)
    piercing = sqlalchemy.Column(sqlalchemy.Integer)


class ItemRangeWeapon(SqlAlchemyBase):
    __tablename__ = "itemRangeWeapon"

    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)

    energyCost = sqlalchemy.Column(sqlalchemy.Integer)
    damage = sqlalchemy.Column(sqlalchemy.Integer)
    piercing = sqlalchemy.Column(sqlalchemy.Integer)
    ammoType = sqlalchemy.Column(sqlalchemy.String)
    hitChance = sqlalchemy.Column(sqlalchemy.Integer) # %


class ItemAmmo(SqlAlchemyBase):
    __tablename__ = "itemAmmo"

    name = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)