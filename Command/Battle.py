import logging
from pprint import pprint

from data import __all_models, db_session
import random
import json

import Command.commands

log = logging.getLogger()
base_session = {"members": []}



# {<Battle ID>: {"members": ["name1", "name2"], "type": "pvp"/"pve", "turn": 0}}
battle_sessions = {}

# {<Battle ID>: {"dmg": 30, "energy": 5, "energy_cost": 2, "hp": 100, "def": 10}}
bots = {}



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
        melee - статы оружия ближнего боя
        range - статы оружия дальнего боя
        eng - сколько осталось энергии
        ha - heal amount
        def - defence

    :param key: ключ
    :param username: имя пользователя
    """
    if key == "ha":
        return get_heal_amount(username)
    if key == "melee":
        return get_melee(username)
    if key == "range":
        return get_range(username)
    if key == "def":
        return get_defence(username)
    if key == "eng":
        return get_energy(username)
    if key == "hp":
        return get_hp(username)
    return -1

def get_heal_amount(username):
    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)

    equipment = json.loads(user_params.equipment)

    if equipment["ItemHeal"][0] <= 0:
        return -1

    heal_name = equipment["ItemHeal"][1]
    heal = db_sess.query(__all_models.ItemHeal).get(heal_name)

    if heal is None:
        return -1

    heal_amount = heal.healAmount
    equipment["ItemHeal"][0] -= 1
    user_params.equipment = json.dumps(equipment)

    db_sess.commit()

    return heal_amount

def get_melee(username):
    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)
    equipment = json.loads(user_params.equipment)

    if equipment["ItemMeleeWeapon"] == "":
        return -1

    weapon_name = equipment["ItemMeleeWeapon"]
    weapon = db_sess.query(__all_models.ItemMeleeWeapon).get(weapon_name)

    if weapon is None:
        return -1

    output = {"dmg": weapon.damage, "eng": weapon.energyCost, "prc": weapon.piercing, "ch": 100}
    return output

def get_range(username):
    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)
    equipment = json.loads(user_params.equipment)

    if equipment["ItemRangeWeapon"] == "":
        return -1

    weapon_name = equipment["ItemRangeWeapon"]
    weapon = db_sess.query(__all_models.ItemRangeWeapon).get(weapon_name)

    if weapon is None:
        return -1

    output = {"dmg": weapon.damage, "eng": weapon.energyCost, "prc": weapon.piercing, "ch": weapon.hitChance}
    return output

def get_defence(username):
    defence = 0
    defence += Command.commands.get_user_params(username)["defence"]

    user_params = db_session.create_session().query(__all_models.UsersParams).get(username)
    armors = db_session.create_session().query(__all_models.ItemArmor)
    armor = json.loads(user_params.equipment)["ItemArmor"]
    armor_defence = []

    for item in armors:
        if Command.commands.localize(item.name, username) in armor.values():
            armor_defence.append(item.defence)

    defence += sum(armor_defence) ** 0.5

    return defence if defence != 0 else 1

def get_energy(username):
    user_params = db_session.create_session().query(__all_models.UsersParams).get(username)
    return json.loads(user_params.stats)["energy"]

def get_hp(username):
    return Command.commands.get_user_params(username)["hp"]

def turn_check(username):
    battle_id = get_battle_id(username)

    if battle_sessions[battle_id]["members"][battle_sessions[battle_id]["turn"]] == username \
            and (len(battle_sessions[battle_id]["members"]) >= 2 or
                 battle_sessions[battle_id]["type"] == "pve"):
        return True
    return False

def send_message(username, text):
    from app import get_vars, set_vars

    dct = get_vars().copy()
    dct["console_outputs"][Command.commands.encode_name(username)].append(text)
    set_vars(dct)


def create(username, *args):
    if len(args) < 1:
        return Command.commands.localize("BTL_CREATE_NO_TYPE", username)

    lobby_type = args[0]

    battle_id = random.randint(0, 1000)
    while battle_id in battle_sessions.keys():
        battle_id = random.randint(0, 1000)

    battle_sessions[battle_id] = {"members": [], "type": "pvp" if lobby_type == "pvp" else "pve", "turn": 0}
    enter(username, battle_id)

    if battle_sessions[battle_id]["type"] == "pve":
        weapon = get_battle_stats("melee", username)
        if weapon == -1:
            weapon = get_battle_stats("range", username)
        if weapon == -1:
            weapon = {"dmg": 1}
        print(weapon)

        bots[battle_id] = {"dmg": weapon["dmg"] * 1.2,
                           "def": get_battle_stats("def", username) * 1.2,
                           "energy": 5,
                           "energy_cost": 2,
                           "hp": 100}
        bots[battle_id]["money"] = bots[battle_id]["dmg"] * bots[battle_id]["def"]

    return Command.commands.localize("BTL_CREATE_SUCCESS", username, args=[battle_id, battle_sessions[battle_id]['type']])


def turn(battle_id):
    battle_sessions[battle_id]["turn"] = (battle_sessions[battle_id]["turn"] + 1) % 2

    if battle_sessions[battle_id]["type"] == "pve" and battle_sessions[battle_id]["turn"] == 1:
        pve_turn(battle_id)


def pve_turn(battle_id):
    bot = bots[battle_id]

    if bot["energy"] < bot["energy_cost"]:
        bot_pass(battle_id)
    else:
        bot_attack(battle_id)

    turn(battle_id)


def enter(username, *args):
    if len(args) < 1:
        return Command.commands.localize("BTL_ENTER_NO_ID", username)
    if not str(args[0]).isdigit():
        return Command.commands.localize("BTL_ENTER_INVALID_ID", username)

    battle_id = int(args[0])
    set_battle_id(username, battle_id)

    if battle_id not in battle_sessions.keys():
        battle_sessions[battle_id] = base_session
    battle_sessions[battle_id]["members"].append(username)

    send_message(username, Command.commands.localize("BTL_ENTER_SUCCESS", username, args=[battle_id]))


def leave(username):
    battle_id = get_battle_id(username)
    battle_sessions[battle_id]["members"].remove(username)
    if len(battle_sessions[battle_id]) <= 0:
        battle_sessions.pop(battle_id)

    set_battle_id(username, -1)
    restore(username)


def escape(username):
    if not turn_check(username):
        return Command.commands.localize("BTL_ESC_NOT_TURN", username)

    chance = random.random() * 100

    if chance > 50:
        if battle_sessions[get_battle_id(username)]["type"] == "pvp":
            send_message(get_enemy(username, get_battle_id(username)), Command.commands.localize("BTL_ESC_TO_ENEMY", get_enemy(username, get_battle_id(username))))
            leave(get_enemy(username, get_battle_id(username)))

        leave(username)


        return Command.commands.localize("BTL_ESC_SUCCESS", username)
    turn(get_battle_id(username))
    return Command.commands.localize("BTL_ESC_UNSUCCESS", username)


def attack(username, *args):
    if not turn_check(username):
        return Command.commands.localize("BTL_ATK_NOT_TURN", username)

    battle_id = get_battle_id(username)
    turn(battle_id)
    lobby_type = battle_sessions[battle_id]["type"]


    if lobby_type == "pvp":
        enemy = get_enemy(username, battle_id)
        if len(args) < 1:
            send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
            return Command.commands.localize("BTL_ATK_NO_TYPE", username)
        attack_type = args[0]

        if attack_type == "melee":
            send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
            weapon = get_battle_stats("melee", username)
        elif attack_type == "range":
            send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
            weapon = get_battle_stats("range", username)
        else:
            send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
            return Command.commands.localize("BTL_ATK_INVALID_TYPE", username)
        if weapon == {}:
            send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
            return Command.commands.localize("BTL_ATK_NO_WEAP", username)

        if get_battle_stats("eng", username) < weapon["eng"]:
            send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
            return Command.commands.localize("BTL_ATK_LESS_ENG", username, args=[str(weapon["eng"] - get_battle_stats("eng", username))])

        Command.commands.edit_user_stats("energy", -weapon["eng"], "+", username)

        dmg = weapon["dmg"] + Command.commands.get_user_params(username)["attack"]

        if random.randint(0, 100) <= round(dmg * weapon["prc"] * weapon["ch"] / get_battle_stats("def", enemy) / 100):
            dmg /= get_battle_stats("def", enemy)
            Command.commands.edit_user_stats("hp", round(-dmg), "+", enemy)

            send_message(enemy, Command.commands.localize("BTL_ATK_ENEMY_ATK", enemy, args=[dmg]))

            result = death_check(battle_id)
            if result:
                Command.commands.edit_user_stats("money",
                                                 Command.commands.get_user_params(
                                                     enemy)["money"] // 4,
                                                 "+", username)
                Command.commands.edit_user_stats("money",
                                                 -Command.commands.get_user_params(
                                                     enemy)["money"] // 4,
                                                 "+", enemy)
                leave(username)
                leave(enemy)

            return Command.commands.localize("BTL_ATK_SUCCESS_ATK", username, args=[str(dmg)])
        send_message(enemy, Command.commands.localize("BTL_ATK_SKIP_TO_ENEMY", enemy))
        return Command.commands.localize("BTL_ATK_UNSUCCESS_ATK", username)

    if len(args) < 1:
        return Command.commands.localize("BTL_ATK_NO_TYPE", username)
    attack_type = args[0]

    if attack_type == "melee":
        weapon = get_battle_stats("melee", username)
    elif attack_type == "range":
        weapon = get_battle_stats("range", username)
    else:
        return Command.commands.localize("BTL_ATK_INVALID_TYPE", username)
    if weapon == {}:
        return Command.commands.localize("BTL_ATK_NO_WEAP", username)

    if get_battle_stats("eng", username) < weapon["eng"]:
        return Command.commands.localize("BTL_ATK_LESS_ENG", username,
                                         args=[str(weapon["eng"] - get_battle_stats("eng", username))])

    Command.commands.edit_user_stats("energy", -weapon["eng"], "+", username)

    dmg = weapon["dmg"] + Command.commands.get_user_params(username)["attack"]

    if random.randint(0, 100) <= \
            round(dmg * weapon["prc"] * weapon["ch"] / bots[battle_id]["def"] / 100):

        bots[battle_id]["hp"] -= round(dmg)

        result = death_check(battle_id)

        if result:
            Command.commands.edit_user_stats("money",
                                             bots[battle_id]["money"] // 1,
                                             "+", username)

            leave(username)

        return Command.commands.localize("BTL_ATK_SUCCESS_ATK", username, args=[str(dmg)])
    return Command.commands.localize("BTL_ATK_UNSUCCESS_ATK", username)


def heal(username, *args):
    if not turn_check(username):
        return Command.commands.localize("BTL_HEAL_NOT_TURN", username)
    turn(get_battle_id(username))

    heal_amount = get_battle_stats("ha", username)

    if heal_amount == -1:
        send_message(get_enemy(username, get_battle_id(username)), "Your enemy skipped turn")
        return Command.commands.localize("BTL_HEAL_ERR", username)

    Command.commands.edit_user_stats("hp", heal_amount, "+", username)

    if Command.commands.get_user_params(username)["hp"] > 100:
        heal_amount = 100 - heal_amount
        Command.commands.edit_user_stats("hp", 100, "=", username)

    if battle_sessions[get_battle_id(username)]["type"] == "pvp":
        send_message(get_enemy(username, get_battle_id(username)),
                     Command.commands.localize("BTL_HEAL_SUCC_TO_ENEM",
                                               get_enemy(username, get_battle_id(username)), args=[heal_amount]))

    return Command.commands.localize("BTL_HEAL_SUCC", username, args=[str(heal_amount),
                                                                      str(Command.commands.get_user_params(username)["hp"])])


def battle_pass(username, *args):
    if not turn_check(username):
        return Command.commands.localize("BTL_PASS_NOT_TURN", username)
    turn(get_battle_id(username))

    energy_regenerated = 10
    Command.commands.edit_user_stats("energy", energy_regenerated, "+", username)

    if battle_sessions[get_battle_id(username)]["type"] == "pvp":
        send_message(get_enemy(username, get_battle_id(username)), Command.commands.localize("BTL_PASS_SKIP_TO_ENEM", get_enemy(username, get_battle_id(username))))
    return Command.commands.localize("BTL_PASS_REGEN", username, args=[energy_regenerated])


def bot_attack(battle_id):
    username = battle_sessions[battle_id]["members"][0]
    bot = bots[battle_id]

    dmg = bot["dmg"] / (get_battle_stats("def", username) ** 0.5)

    Command.commands.edit_user_stats("hp", round(-dmg), "+", username)

    send_message(username, Command.commands.localize("BTL_BOT_ATK", username, args=[dmg]))


def bot_pass(battle_id):
    bot = bots[battle_id]

    bot["energy"] += 5

    send_message(battle_sessions[battle_id]["members"][0], Command.commands.localize("BTL_BOT_PASS", battle_sessions[battle_id]["members"][0]))


def death_check(battle_id):
    lobby_type = battle_sessions[battle_id]["type"]

    if lobby_type == "pve":
        print(bots[battle_id]["hp"], get_battle_stats("hp", battle_sessions[battle_id]["members"][0]))
        if bots[battle_id]["hp"] <= 0:
            send_message(battle_sessions[battle_id]["members"][0],  "You won!")
            return True

        player = battle_sessions[battle_id]["members"][0]
        if get_battle_stats("hp", player) <= 0:
            send_message(player, "You lost...")
            return True
    else:
        players = battle_sessions[battle_id]["members"]

        for player in players:
            if get_battle_stats("hp", player) <= 0:
                send_message(player, "You lost...")
                send_message(players.copy().remove(player)[0], "You won!")
                return True
    return False


def restore(username):
    Command.commands.edit_user_stats("energy", 10, "=", username)
    Command.commands.edit_user_stats("hp", 100, "=", username)