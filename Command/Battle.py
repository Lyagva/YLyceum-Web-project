import logging
from data import __all_models, db_session
import random
import json

import Command.commands

log = logging.getLogger()
base_session = {"members": []}
battle_sessions = {-228: {"members": ["name1", "name2"]}}


def get_battle_id(username):
    return db_session.create_session().query(__all_models.UsersParams).get(username).battle_id

def set_battle_id(username, battle_id):
    db_sess = db_session.create_session()
    user_params = db_sess.query(__all_models.UsersParams).get(username)
    user_params.battle_id = battle_id
    db_sess.commit()

def get_enemy(username, battle_id):
    session = battle_sessions[battle_id]

    if len(session) >= 2:
        session = session.copy()
        session["members"].remove(username)
        return session["members"][0]
    return None

def get_battle_stats(key, username):
    """
    Функция выводит боевые статы [username]'а по ключу [key]
    Ключи:
        melee - урон в ближнем бою
        range - урон от огнестрела
        eng - сколько осталось энергии
        ha - heal amount

    :param key: ключ
    :param username: имя пользователя
    """
    if key == "ha":
        return get_heal_amount(username)
    if key == "melee":
        return get_melee(username)
    if key == "range":
        return get_range(username)

def get_heal_amount(username):
    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)

    equipment = json.loads(user_params.equipment)

    if equipment["ItemHeal"][0] <= 0:
        return -1

    heal_name = equipment["ItemHeal"][1]

    heals = db_sess.query(__all_models.ItemHeal).all()

    heal_amount = -1
    for item in heals:
        if Command.commands.localize(item.name, username) == heal_name:
            heal_amount = item.healAmount
            equipment["ItemHeal"][0] -= 1
            user_params.equipment = json.dumps(equipment)
            break

    db_sess.commit()

    if heal_amount == -1:
        return -1

    return heal_amount

def get_melee(username):
    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)
    equipment = json.loads(user_params.equipment)

    if equipment["ItemMeleeWeapon"] == "":
        return -1

    weapon_name = equipment["ItemMeleeWeapon"]
    weapons = db_sess.query(__all_models.ItemMeleeWeapon).all()

    output = {}
    for item in weapons:
        if Command.commands.localize(item.name, username) == weapon_name:
            output = {"dmg": item.damage, "ecost": item.energyCost, "prc": item.piercing}
            break

    db_sess.commit()

    if output == {}:
        return {}
    return output

def get_range(username):
    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)
    equipment = json.loads(user_params.equipment)

    if equipment["ItemRangeWeapon"] == "":
        return -1

    weapon_name = equipment["ItemRangeWeapon"]
    weapons = db_sess.query(__all_models.ItemRangeWeapon).all()

    output = -1
    for item in weapons:
        if Command.commands.localize(item.name, username) == weapon_name:
            output = {"dmg": item.damage, "ecost": item.energyCost, "prc": item.piercing, "hch": item.hitChance}
            break

    db_sess.commit()

    if output == -1:
        return {}
    return output


def turn(battle_id):
    battle_sessions[battle_id]["members"] = battle_sessions[battle_id]["members"][::-1]


def enter(username, *args):
    if len(args) < 1:
        return "No battle id"
    if not args[0].isdigit():
        return "Invalid battle id"

    battle_id = int(args[0])
    set_battle_id(username, battle_id)

    if battle_id not in battle_sessions.keys():
        battle_sessions[battle_id] = base_session
    battle_sessions[battle_id]["members"].append(username)

    return "You entered battle " + str(battle_id)


def leave(username, *args):
    battle_id = get_battle_id(username)
    battle_sessions[battle_id]["members"].remove(username)
    if len(battle_sessions[battle_id]) <= 0:
        battle_sessions.pop(battle_id)

    set_battle_id(username, -1)


def escape(username):
    chance = random.random() * 100

    if chance > 50:
        leave(username)

        return "You successfully escaped battle"
    return "You can't escape battle"


def attack(username, *args):
    if len(args) < 1:
        return "No attack type provided. Use 'melee' or 'range'"
    attack_type = args[0]

    if attack_type == "melee":
        weapon = get_battle_stats("melee", username)
    elif attack_type == "range":
        weapon = get_battle_stats("range", username)
    else:
        return "Invalid attack type"
    if weapon == {}:
        return "No weapon"

    dmg = weapon["dmg"]

    enemy = get_enemy(username, get_battle_id(username))
    Command.commands.edit_user_stats("hp", -dmg, "+", enemy)

    return "Successfully attacked enemy by " + str(dmg) + "HP"


def block(username, *args):
    pass


def heal(username, *args):
    heal_amount = get_battle_stats("ha", username)

    if heal_amount == -1:
        return "Error while healing"

    Command.commands.edit_user_stats("hp", heal_amount, "+", username)

    if Command.commands.get_user_params(username)["hp"] > 100:
        heal_amount = 100 - heal_amount
        Command.commands.edit_user_stats("hp", 100, "=", username)

    return "You successfully healed by " + str(heal_amount) + \
           "HP. Your HP - " + str(Command.commands.get_user_params(username)["hp"])


def battle_pass(username, *args):
    energy_regenerated = 5
    Command.commands.edit_user_stats("energy", energy_regenerated, "+", username)
    return f"Use successfully regenerated {energy_regenerated} energy"