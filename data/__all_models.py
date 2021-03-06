import json
import sqlalchemy
from .db_session import SqlAlchemyBase


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
    }
    stats = sqlalchemy.Column(sqlalchemy.JSON, default=json.dumps(default_stats))

    # [count, durability, table, itemName]
    default_items = {"items": []}
    items = sqlalchemy.Column(sqlalchemy.JSON, default=json.dumps(default_items))
    battle_id = sqlalchemy.Column(sqlalchemy.Integer, default=-1)

    default_equip = {"ItemMeleeWeapon": 'MELEE_RUSTY', "ItemRangeWeapon": 'RANGE_FLINT',
                     "ItemHeal": [10, "ITEM_SMALL_MEDKIT"],
                     "ItemArmor": {"head": '', "torso": 'ITEM_CLOTH_TORSO', "hands": '', "legs": '', "feet": ''}}
    equipment = sqlalchemy.Column(sqlalchemy.JSON, default=json.dumps(default_equip))


class Users(SqlAlchemyBase):
    __tablename__ = "users"

    login = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    password = sqlalchemy.Column(sqlalchemy.String)
    encoded_login = sqlalchemy.Column(sqlalchemy.String)
    personal_key = sqlalchemy.Column(sqlalchemy.String)
    lang = sqlalchemy.Column(sqlalchemy.String, default="EN")
    email = sqlalchemy.Column(sqlalchemy.String)
    friends = sqlalchemy.Column(sqlalchemy.String, default="[]")


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
    hitChance = sqlalchemy.Column(sqlalchemy.Integer)  # %
