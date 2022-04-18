import logging
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
    return -1

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
            output = {"dmg": item.damage, "eng": item.energyCost, "prc": item.piercing, "ch": 100}
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
            output = {"dmg": item.damage, "eng": item.energyCost, "prc": item.piercing, "ch": item.hitChance}
            break

    db_sess.commit()

    if output == -1:
        return {}
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

    return defence

def get_energy(username):
    user_params = db_session.create_session().query(__all_models.UsersParams).get(username)
    return json.loads(user_params.stats)["energy"]

def turn_check(username):
    if battle_sessions[get_battle_id(username)]["members"] \
        [battle_sessions[get_battle_id(username)]["turn"]] == username \
            and (len(battle_sessions[get_battle_id(username)]["members"]) >= 2 or
                 battle_sessions[get_battle_id(username)]["type"] == "pve"):
        return True
    return False

def send_message(username, text):
    from app import console_outputs

    console_outputs[Command.commands.encode_name(username)].append(text)


def create(username, *args):
    if len(args) < 1:
        return "No lobby type provided"

    lobby_type = args[0]

    battle_id = random.randint(0, 1000)
    while battle_id in battle_sessions.keys():
        battle_id = random.randint(0, 1000)

    battle_sessions[battle_id] = {"members": [], "type": "pvp" if lobby_type == "pvp" else "pve"}
    enter(username, battle_id)

    if battle_sessions[battle_id]["type"] == "pve":
        bots[battle_id] = {"dmg": get_battle_stats("melee", username)["dmg"] * 1.2,
                           "def": get_battle_stats("def", username) * 1.2,
                           "energy": 5,
                           "energy_cost": 2,
                           "hp": 100}
        bots[battle_id]["money"] = bots[battle_id]["dmg"] * bots[battle_id]["def"]

    return f"Created lobby {battle_id} with {battle_sessions[battle_id]['type']} type. You already in."


def turn(battle_id):
    battle_sessions[battle_id]["turn"] = (battle_sessions[battle_id]["turn"] + 1) % 2

    if battle_sessions[battle_id]["type"] == "pve" and battle_sessions[battle_id]["turn"] == 1:
        pve_turn(battle_id)


def pve_turn(battle_id):
    bot = bots[battle_id]

    if bot["energy"] < bot["energy_cost"]:
        return_msg = bot_pass(battle_id)
    else:
        return_msg = bot_attack(battle_id)

    send_message(battle_sessions[battle_id]["members"][0], return_msg)
    turn(battle_id)


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

    return f"You entered battle {battle_id}"


def leave(username):
    battle_id = get_battle_id(username)
    battle_sessions[battle_id]["members"].remove(username)
    if len(battle_sessions[battle_id]) <= 0:
        battle_sessions.pop(battle_id)

    set_battle_id(username, -1)


def escape(username):
    if not turn_check(username):
        return "It's not your turn!"

    chance = random.random() * 100

    if chance > 50:
        send_message(get_enemy(username, get_battle_id(username)), "Your enemy escaped from battle")

        leave(username)

        return "You successfully escaped battle"
    return "You can't escape battle"


def attack(username, *args):
    if not turn_check(username):
        return "It's not your turn!"

    battle_id = get_battle_id(username)
    turn(battle_id)
    lobby_type = battle_sessions[battle_id]["type"]


    if lobby_type == "pvp":
        enemy = get_enemy(username, battle_id)
        if len(args) < 1:
            send_message(enemy, "Your enemy skipped turn")
            return "No attack type provided. Use 'melee' or 'range'"
        attack_type = args[0]

        if attack_type == "melee":
            send_message(enemy, "Your enemy skipped turn")
            weapon = get_battle_stats("melee", username)
        elif attack_type == "range":
            send_message(enemy, "Your enemy skipped turn")
            weapon = get_battle_stats("range", username)
        else:
            send_message(enemy, "Your enemy skipped turn")
            return "Invalid attack type"
        if weapon == {}:
            send_message(enemy, "Your enemy skipped turn")
            return "No weapon"

        if get_battle_stats("eng", username) < weapon["eng"]:
            send_message(enemy, "Your enemy skipped turn")
            return "You have less energy than needed. Needed: " + str(weapon["eng"] - get_battle_stats("eng", username))

        Command.commands.edit_user_stats("energy", -weapon["eng"], "+", username)

        dmg = weapon["dmg"] ** 0.5 + Command.commands.get_user_params(username)["attack"]

        if random.randint(0, 100) <= round(dmg * weapon["prc"] * weapon["ch"] / get_battle_stats("def", enemy) / 100):
            dmg /= get_battle_stats("def", enemy)
            Command.commands.edit_user_stats("hp", -dmg, "+", enemy)

            send_message(enemy, f"Your enemy attacked you by {dmg} HP")

            result = death_check(battle_id)
            if result:
                Command.commands.edit_user_stats("money",
                                                 Command.commands.get_user_params(
                                                     enemy)["money"] / 4,
                                                 "+", username)
                Command.commands.edit_user_stats("money",
                                                 -Command.commands.get_user_params(
                                                     enemy)["money"] / 4,
                                                 "+", enemy)
                leave(username)
                leave(enemy)

            return "Successfully attacked enemy by " + str(dmg) + "HP"
        send_message(enemy, "Your enemy skipped turn")
        return "You didn't hit enemy"

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

    if get_battle_stats("eng", username) < weapon["eng"]:
        return "You have less energy than needed. Needed: " + str(weapon["eng"] - get_battle_stats("eng", username))

    Command.commands.edit_user_stats("energy", -weapon["eng"], "+", username)

    dmg = weapon["dmg"] ** 0.5 + Command.commands.get_user_params(username)["attack"]

    if random.randint(0, 100) <= \
            round(dmg * weapon["prc"] * weapon["ch"] / bots[battle_id]["def"] / 100):

        dmg /= bots[battle_id]["def"]
        bots[battle_id]["hp"] -= dmg

        result = death_check(battle_id)

        if result:
            Command.commands.edit_user_stats("money",
                                             bots[battle_id]["money"],
                                             "+", username)

            leave(username)

        return "Successfully attacked enemy by " + str(dmg) + "HP"
    return "You didn't hit enemy"


def heal(username, *args):
    if not turn_check(username):
        return "It's not your turn!"
    turn(get_battle_id(username))

    heal_amount = get_battle_stats("ha", username)

    if heal_amount == -1:
        send_message(get_enemy(username, get_battle_id(username)), "Your enemy skipped turn")
        return "Error while healing"

    Command.commands.edit_user_stats("hp", heal_amount, "+", username)

    if Command.commands.get_user_params(username)["hp"] > 100:
        heal_amount = 100 - heal_amount
        Command.commands.edit_user_stats("hp", 100, "=", username)

    send_message(get_enemy(username, get_battle_id(username)), f"Your enemy successfully healed by {heal_amount} HP")

    return "You successfully healed by " + str(heal_amount) + \
           "HP. Your HP - " + str(Command.commands.get_user_params(username)["hp"])


def battle_pass(username, *args):
    if not turn_check(username):
        return "It's not your turn!"
    turn(get_battle_id(username))

    energy_regenerated = 5
    Command.commands.edit_user_stats("energy", energy_regenerated, "+", username)
    send_message(get_enemy(username, get_battle_id(username)), "Your enemy skipped turn")
    return f"Use successfully regenerated {energy_regenerated} energy"


def bot_attack(battle_id):
    bot = bots[battle_id]

    dmg = bot["dmg"]

    Command.commands.edit_user_stats("hp", -dmg, "+", battle_sessions[battle_id]["members"][0])

    return f"Enemy bot hit you by {dmg} HP"


def bot_pass(battle_id):
    bot = bots[battle_id]

    bot["energy"] += 5

    return "Enemy bot regenerated 5 energy"


def death_check(battle_id):
    lobby_type = battle_sessions[battle_id]["type"]

    if lobby_type == "pve":
        if bots[battle_id]["health"] <= 0:
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