import logging
from data import __all_models, db_session
import json

log = logging.getLogger()

# ======== COMMANDS GLOBAL FUNCS ========
def get_all_commands():
    from app import log
    command_list = []

    log.debug("Opening db session for GETTING ALL COMMANDS")
    db_sess = db_session.create_session()
    for value in db_sess.query(__all_models.Commands).all():
        command_list.append((value.name, value.syntax, value.description, value.python_func))

    return command_list

def process_command(addr, text):
    # Importing LOG from app.py
    import app
    global log
    log = app.log


    all_commands = get_all_commands()
    command, *args = text.lower().split()

    for db_command in all_commands:
        if command == db_command[0]:
            log.debug(f"found command {command} in all commands list")
            args = [f"'{arg}'" for arg in args]

            log.debug(f"Executing {command} for {addr}")
            return eval(f"{db_command[3]}('{addr}', {', '.join(args)})")

    log.debug(f"Can't find {command} for {addr}")
    return f"command \"{command}\" not found. Use help to get all commands"


# ======== LOCALIZATION ========
special_symbols = {"~n": "\n", "~t": "\t"}
SELL_PRICE_DIVIDER = 1.2


def localize(code, addr, args=None):
    if args is None:
        args = []

    from csv import reader

    args = list(map(str, args))

    lang = "EN"
    username = get_user_by_ip(addr)
    if username is not None:
        for user in get_users():
            if user.login == username:
                # log.debug(f"Setting lang to {user.lang}")
                lang = user.lang



    # Reading csv file
    # log.debug("Opening and reading loc file")
    with open('csv/localizations.csv', encoding="utf8") as csvfile:
        reader = reader(csvfile, delimiter=';', quotechar='"')
        data = list(map(lambda x: x, reader)) # Storing data to list

    keys = {}
    for i, value in enumerate(data[0]):
        keys[value] = i # getting keys dict {<header>: <ind>}
    phrases = data[1:] # getting all phrases

    for line in phrases: # going through all lines
        if code == line[0]: # check if line.code == code
            # log.debug(f"Found {code} in loc.csv")

            output = str(line[keys[lang]]) # setting output

            # log.debug(f"Replacing special symbols for {output}")
            for key in special_symbols.keys():
                output = output.replace(key, special_symbols[key])

            # log.debug(f"Placing {args} to line")
            for i in range(min(output.count("{}"), len(args))):
                output = output.replace("{}", args[i], 1)

            # log.debug(f"Returning {output} phrase")
            return output

    # log.debug(f"Loc code {code} not found")
    return code


def get_all_langs():
    from csv import reader

    # log.debug("Opening and reading localizations file")
    with open('csv/localizations.csv', encoding="utf8") as csvfile:
        reader = reader(csvfile, delimiter=';', quotechar='"')
        data = list(map(lambda x: x, reader)) # Storing data to list

    keys = []
    for value in data[0][1:]:
        keys.append(str(value))

    # log.debug(f"Returning all langs: {keys}")
    return keys


# ======== LOGIN AND USERS ========
def get_user_friends(addr):
    username = get_user_by_ip(addr)
    user = None

    for usr in get_users():
        if usr.login == username:
            user = usr
            break

    if user and user.friends:
        log.debug(f"Found friends for {user.login}, {addr}. Friends: {eval(user.friends)}")
        return eval(user.friends)

    return []


def get_users():
    log.debug("(One action) Getting all users. Accessing main.db . Returning all users")
    return list(map(lambda user: user, db_session.create_session().query(__all_models.Users).all()))


def get_all_users_params():
    log.debug("(One action) Getting all user params. Accessing main.db . Returning all user params")
    return list(map(lambda user_p: user_p, db_session.create_session().query(__all_models.UsersParams).all()))


def get_user_by_ip(addr):
    log.debug("Getting all users")
    for user in get_users():
        if user.ip == addr:
            log.debug(f"User {user.login} found by {addr}")
            return user.login
    return None


def get_ip_by_user(name):
    log.debug("Getting all users")
    for user in get_users():
        if user.login == name:
            if user.ip:
                log.debug(f"User {user.login} found by {name}")
                return user.ip
    return None


def get_user_params(addr="", username=""):
    if addr:
        username = get_user_by_ip(addr)
    elif username is None:
        log.debug(f"Can't find user {username}, {addr}")
        return None

    log.debug(f"Getting {username} params")
    for user_p in get_all_users_params():
        if user_p.name == username:
            log.debug(f"Params for {username} found")

            return json.loads(user_p.stats)

    log.debug(f"Can't find params for user {username}")
    return None


def edit_user_stats(key, value, type="+", addr="", username=""):
    # type
    # + add, = set, * mul
    if addr:
        username = get_user_by_ip(addr)
    elif username is None:
        log.debug(f"Can't find user {username}, {addr}")
        return

    log.debug(f"Getting user params for {username}")
    stats = get_user_params(username=username)


    log.debug(f"Applying '{type}{value}' operation for {key} param for {username}, {addr}")
    if type == "+":
        stats[key] += value
    elif type == "-":
        stats[key] -= value
    elif type == "*":
        stats[key] *= value
    elif type == "=":
        stats[key] = value


    log.debug("Opening main.db session")
    db_sess = db_session.create_session()

    log.debug(f"Getting user params by name {username}, {addr}")
    user_params = db_sess.query(__all_models.UsersParams).get(username)
    log.debug(f"Editing {username}, {addr} params to '{stats}'")
    user_params.stats = json.dumps(stats)

    log.debug(f"Appending data to main.db for user {username}, {addr}")
    db_sess.add(user_params)
    log.debug("Closing main.db")
    db_sess.commit()


def clear_old_data_ip(addr):
    log.debug("Opening main.db session")
    db_sess = db_session.create_session()

    username = get_user_by_ip(addr)
    if username:
        log.debug(f"Opening main.db to get {username}, {addr} user data")
        prev_user = db_sess.query(__all_models.Users).get(username)
        log.debug("Clearing data for {username}, {addr}")
        prev_user.ip = None

    log.debug("Closing main.db")
    db_sess.commit()


def send_user_password(addr, user):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    import os
    from dotenv import load_dotenv
    from cryptography.fernet import Fernet

    log.debug(f"Recovering password for {addr}")

    message = f'''
    Hello. 
    You have requested password recovery from account {user.login} in the Lambda-14 game. 
    Your password: {Fernet(user.key_code_password).decrypt(user.password).decode('utf-8')}
    '''
    try:
        # setup the parameters of the message

        load_dotenv()
        password = os.getenv('EMAIL_PASSWORD')

        # create server
        server = smtplib.SMTP('smtp.gmail.com: 587')

        server.starttls()

        msg = MIMEMultipart()

        msg['From'] = 'lambda.games.supp@gmail.com'
        msg['Subject'] = "Password recovery"

        msg['To'] = user.email

        msg.attach(MIMEText(message, 'plain'))

        # Login Credentials for sending the mail
        server.login(msg['From'], password)

        # send the message via the server.
        server.sendmail(msg['From'], msg['To'], msg.as_string())
    except Exception as e:
        return localize("PASSWORD_RECOVERY_EMAIL_NOT_VALID", addr)

    return localize("PASSWORD_RECOVERY_SUCCESS_SEND_MAIL", addr, args=[user.login])


def command_password_recovery(addr, *args):
    log.debug(f"[Command password recovery {addr}] Executing")

    if len(args) < 1:
        log.debug(f"[Password Recovery {addr}] No username provided")
        return localize("PASSWORD_RECOVERY_NO_USERNAME", addr)

    username = args[0]

    user = None
    for usr in get_users():
        if usr.login == username:
            user = usr

    if user is None:
        log.debug(f"[Password Recovery {addr}] Can't find user")
        return localize("PASSWORD_RECOVERY_NO_USER_IN_DB", addr, args=[username])

    if not user.email:
        log.debug(f"[Password Recovery {addr}] No email for {username} user")
        return localize("PASSWORD_RECOVERY_NO_USER_EMAIL", addr, args=[username])

    log.debug(f"[Password Recovery {addr}] Sending email with {username} user")
    return send_user_password(addr, user)


# ======== CONSOLE COMMANDS ========
def command_help(addr, *args):
    log.debug(f"[Command help {addr}] Executing")

    return_data = localize("HELP_HEADER", addr)

    log.debug(f"[Command help {addr}] Getting all commands")
    for command in get_all_commands():
        description = localize(command[2], addr)
        return_data += localize("HELP_FORMAT", addr, args=[command[0], command[1], description])

    log.debug(f"[Command help {addr}] Returning data")
    return return_data


def command_debug(addr, *args):
    from datetime import datetime

    log.debug(f"[Command debug {addr}] Executing")

    return_data = f"sender address \t {addr}\n"
    return_data += f"server time \t {datetime.now()}\n"
    return_data += f"user \t {get_user_by_ip(addr) if get_user_by_ip(addr) else 'user not found'}"

    return return_data


def command_clear(addr, *args):
    log.debug(f"[Command clear {addr}] Executing")

    return "!!clear"


def command_lang(addr, *args):
    log.debug(f"[Command lang {addr}] Executing")

    all_langs = map(lambda x: x.lower(), get_all_langs())

    if len(args) < 1:
        log.debug(f"[Command lang {addr}] No lang provided")
        return localize("LANG_NO_LANG", addr, args=[", ".join(all_langs)])
    lang = args[0]

    if lang not in all_langs:
        log.debug(f"[Command lang {addr}] Can't find '{lang}' lang")
        return localize("LANG_INCORRECT", addr, args=[lang])

    log.debug(f"[Command lang {addr}] Opening main.db")
    db_sess = db_session.create_session()
    log.debug(f"[Command lang {addr}] Getting user")
    user = db_sess.query(__all_models.Users).filter_by(ip=addr).first()
    log.debug(f"[Command lang {addr}] Setting lang")
    user.lang = lang.upper()
    log.debug(f"[Command lang {addr}] Commiting to main.db")
    db_sess.commit()

    return localize("LANG_SUCCESS", addr, args=[lang])


def command_status(addr, *args):
    log.debug(f"[Command status {addr}] Executing")
    if len(args) < 1:
        log.debug(f"[Command status {addr}] No username provided")
        return localize("STATUS_NO_USER", addr)

    username = args[0]
    if username == "self":
        username = get_user_by_ip(addr)

    log.debug(f"[Command status {addr}] Getting params for {username}")
    user_params = get_user_params(username=username)

    if user_params is None:
        log.debug(f"[Command status {addr}] Cant find {username} user in params table")
        return localize("STATUS_NO_USER_IN_BD", addr, args=[username])

    return_data = []
    for key, val in user_params.items():
        return_data.append(f'{key}: {val}')

    log.debug(f"[Command status {addr}] Returning user params")
    return '\n'.join(return_data)


def command_wiki(addr, *args):
    log.debug(f"[Command wiki {addr}] Executing")
    if len(args) == 0:
        log.debug(f"[Command wiki {addr}] No argument provided")
        return localize("WIKI_HELP", addr)

    category = args[0]

    if category == "all":
        log.debug(f"[Command wiki {addr}] Requesting all wikis")
        return wiki_material(addr) + wiki_ammo(addr) + wiki_heal(addr) + \
               wiki_armor(addr) + wiki_melee(addr) + wiki_range(addr)

    log.debug(f"[Command wiki {addr}] Requesting {category} wiki")
    if category == "ammo":
        return wiki_ammo(addr)
    if category == "armor":
        return wiki_armor(addr)
    if category == "heal":
        return wiki_heal(addr)
    if category == "material":
        return wiki_material(addr)
    if category == "melee":
        return wiki_melee(addr)
    if category == "range":
        return wiki_range(addr)

    log.debug(f"[Command wiki {addr}] Can't find {category} category")
    return localize("WIKI_INCORRECT_CATEGORY", addr)


def command_inv(addr, *args):
    log.debug(f"[Command inv {addr}] Executing")

    log.debug(f"[Command inv {addr}] Requesting inventory")
    inventory = get_items_by_user(addr)


    outputText = "======== INVENTORY ========\nname \t count\n"
    for item in inventory:
        outputText += f"{localize(item[2], addr)} \t {item[0]}\n"

    log.debug(f"[Command inv {addr}] Returning items")
    return outputText


def command_login(addr, *args):
    from cryptography.fernet import Fernet

    log.debug(f"[Command login {addr}] Executing")

    if len(args) >= 1:
        username = args[0]
    else:
        log.debug(f"[Command login {addr}] No username provided")
        return localize('LOGIN_NO_NAME', addr)

    if len(args) >= 2:
        password = args[1]
    else:
        log.debug(f"[Command login {addr}] No password provided")
        return localize('LOGIN_NO_PASSWORD', addr)

    if username in ["self"]:
        return localize("LOGIN_INCORRECT_NAME", addr)

    for user in get_users():
        if user.login != username:
            continue

        if Fernet(user.key_code_password).decrypt(user.password).decode('utf-8') != password:
            log.debug(f"[Command login {addr}] Incorrect password {password}")
            return localize('LOGIN_INCORRECT_PASSWORD', addr, args=[username])
        else:
            log.debug(f"[Command login {addr}] Clearing old ip")
            clear_old_data_ip(addr)

            log.debug(f"[Command login {addr}] Accessing main.db, editing and saving")
            db_sess = db_session.create_session()
            user = db_sess.query(__all_models.Users).get(user.login)
            user.ip = addr
            db_sess.commit()

            return localize('LOGIN_SUCCESS', addr, args=[username])

    # ======== REGISTRATION ========

    clear_old_data_ip(addr)

    key = Fernet.generate_key()

    user = __all_models.Users()
    user.login = username
    user.key_code_password = key
    user.password = Fernet(key).encrypt(bytes(password, 'utf-8'))
    user.ip = addr


    # Params
    user_params = __all_models.UsersParams()
    user_params.name = username

    # Dumping to DB
    db_sess = db_session.create_session()

    db_sess.add(user)
    db_sess.add(user_params)
    db_sess.commit()

    return localize('LOGIN_NEW_ACC_SUCCESS', addr, args=[username])


def command_email(addr, *args):
    if len(args) < 1:
        return localize("EMAIL_NO_FOUND", addr)

    username = get_user_by_ip(addr)
    if username is None:
        return localize("EMAIL_NO_LOGGED", addr)

    email = args[0]
    db_sess = db_session.create_session()
    for user in db_sess.query(__all_models.Users).all():
        if user.login == username:
            user.email = email
    db_sess.commit()
    return localize("EMAIL_ADD_SUCCESS", addr, args=[email, username])



# ======== SHOP ========
def get_shop_items(addr):
    log.debug(f"Getting shop items")
    return list(map(lambda category: {category: list(map(lambda item: item, db_session.create_session().query(eval('__all_models.' + category)).all()))}, ['ItemMaterial', 'ItemHeal', 'ItemArmor', 'ItemMeleeWeapon', 'ItemRangeWeapon', 'ItemAmmo']))


def command_buy(addr, *args):
    log.debug(f"[Command buy {addr}] Executing")
    if len(args) < 1:
        log.debug(f"[Command buy {addr}] No item provided")
        return localize("BUY_NO_ITEM_PROVIDED", addr)

    item_name = " ".join(args[:len(args) - 1])

    if len(args) > 1:
        if args[-1].isnumeric():
            count = int(args[-1])
        else:
            return localize("BUY_INVALID_COUNT", addr)
    else:
        count = 1

    log.debug(f"[Command buy {addr}] Getting all items")
    lst = get_shop_items(addr)

    for i in lst:
        for category, items in i.items():
            for item in items:
                if item_name == localize(item.name, addr).lower():

                    user_money = get_user_params(get_user_by_ip(addr))['money']

                    if user_money < item.price:
                        return localize("BUY_NO_MONEY", addr)

                    while item.price * count > user_money:
                        count -= 1

                    cost = item.price * count

                    edit_user_stats("money", cost, type="-", addr=addr)

                    add_item = [count, category, vars(item)['name']]
                    add_item_by_ip(add_item, addr)  # [1, 'itemMaterial', 'ITEM_MATERIAL_DEBUG_NAME']

                    return localize("BUY_SUSSESS", addr, args=[count, item_name, cost])

    return localize("BUY_NO_ITEM_FOUND", addr, args=[item_name])


def command_sell(addr, *args):
    if len(args) < 1:
        return localize("SELL_NO_ITEM_PROVIDED", addr)

    item_name = " ".join(args[0:len(args) - 1])

    if len(args) > 1:
        if args[-1].isnumeric():
            count = int(args[-1])
        else:
            return localize("SELL_INVALID_COUNT", addr)
    else:
        count = 1

    inventory = get_items_by_user(addr=addr)

    for item in inventory:
        if item_name == localize(item[2], addr).lower():
            count = min(count, int(item[0]))

            item[0] = -count

            class_name = item[1][0].upper() + item[1][1:]
            price = list(filter(lambda x: x.name == item[2],
                                db_session.create_session().query(eval('__all_models.' + class_name))))[0].price

            cost = int(price * count // SELL_PRICE_DIVIDER)

            edit_user_stats("money", cost, type="+", addr=addr)

            add_item_by_ip(item, addr=addr)  # добавляем в инвентарь отрицательное количество предмета

            return localize("SELL_SUCCESS", addr, args=[count, item_name, cost])

    return localize("SELL_NO_ITEM_FOUND", addr, args=[item_name])


# ======== WIKI ========
def wiki_ammo(addr):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemAmmo).all()))
    outputText = ""

    # AMMO
    outputText += "======== AMMO ========\n"
    outputText += "name \t description \t price buy/sell \n"
    for item in items:
        info = [localize(item.name, addr), localize(item.description, addr), f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}']
        outputText += localize("WIKI_AMMO_FORMAT", addr, args=info) + "\n"

    return outputText


def wiki_armor(addr):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemArmor).all()))
    outputText = ""

    # ARMOR
    outputText += "======== ARMOR ========\n"
    outputText += "name \t description \t price buy/sell \t slot \t defence \n"
    for item in items:
        info = [localize(item.name, addr), localize(item.description, addr), f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}', item.slot, item.defence]
        outputText += localize("WIKI_ARMOR_FORMAT", addr, args=info) + "\n"

    return outputText


def wiki_heal(addr):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemHeal).all()))
    outputText = ""

    # HEAL
    outputText += "======== HEAL ========\n"
    outputText += "name \t description \t price buy/sell \t heal amount \n"
    for item in items:
        info = [localize(item.name, addr), localize(item.description, addr), f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}', item.healAmount]
        outputText += localize("WIKI_HEAL_FORMAT", addr, args=info) + "\n"

    return outputText


def wiki_material(addr):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemMaterial).all()))
    outputText = ""

    # MATERIAL
    outputText += "======== MATERIAL ========\n"
    outputText += "name \t description \t price buy/sell \n"
    for item in items:
        info = [localize(item.name, addr), localize(item.description, addr), f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}']
        outputText += localize("WIKI_MATERIAL_FORMAT", addr, args=info) + "\n"

    return outputText


def wiki_melee(addr):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemMeleeWeapon).all()))
    outputText = ""

    # MELEE
    outputText += "======== MELEE WEAPON ========\n"
    outputText += "name \t description \t price buy/sell \t energy cost \t damage \t piercing \n"
    for item in items:
        info = [localize(item.name, addr), localize(item.description, addr), f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}',
                item.energyCost, item.damage, item.piercing]
        outputText += localize("WIKI_MELEE_FORMAT", addr, args=info) + "\n"

    return outputText


def wiki_range(addr):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemRangeWeapon).all()))
    outputText = ""

    # RANGE
    outputText += "======== RANGE WEAPON ========\n"
    outputText += "name \t description \t price buy/sell \t energy cost \t damage \t piercing \t ammo \t hit chance \n"
    for item in items:
        info = [localize(item.name, addr), localize(item.description, addr), f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}',
                item.energyCost, item.damage, item.piercing, item.ammoType, item.hitChance]
        outputText += localize("WIKI_RANGE_FORMAT", addr, args=info) + "\n"

    return outputText


# ======== Inventory ========
def get_items_by_user(addr=None, username=""):
    if addr:
        username = get_user_by_ip(addr)
    elif username == "":
        return {"items": []}

    inventory = db_session.create_session().query(__all_models.UsersParams).get(username)

    if inventory is None:
        # Params
        user_params = __all_models.UsersParams()
        user_params.name = username

        # Dumping to DB
        db_sess = db_session.create_session()

        db_sess.add(user_params)
        db_sess.commit()

        return []

    return json.loads(inventory.items)["items"]


def add_item_by_ip(item, addr="", username=""):
    # Item
    # [count, durability, table, name]

    if addr != "":
        username = get_user_by_ip(addr)
    elif username == "":
        return "No user provided"

    db_sess = db_session.create_session()

    # Getting params
    if username not in list(map(lambda x: x.name, get_all_users_params())):
        userParams = __all_models.UsersParams()
    else:
        userParams = db_sess.query(__all_models.UsersParams).get(username)

    # Getting inventory
    inventory = get_items_by_user(username=username)

    # Check if item already in inventory
    for index, invItem in enumerate(inventory):
        if item[1] == invItem[1]:
            if item[1] in ["ItemMaterial", "ItemAmmo", "ItemHeal"]:  # Stackable items
                invItem[0] += item[0]
                if invItem[0] <= 0:
                    inventory.pop(index)
                else:
                    inventory[index] = invItem
            else:
                inventory.append(item)

            userParams.items = json.dumps({"items": inventory})
            db_sess.commit()
            return

    inventory.append(item)
    userParams.items = json.dumps({"items": inventory})
    db_sess.commit()



# ======== Chat ========
def command_chat(addr, *args):
    if len(args) == 0:
        return localize("CHAT_NO_FUNC", addr=addr)
    func = args[0]

    if func not in ["add", "remove"]:
        return localize("CHAT_INVALID_FUNC", addr=addr)

    if len(args) <= 1:
        return localize("CHAT_NO_NAME", addr=addr)
    chatter_name = args[1]


    if func == "add":
        if chatter_name not in list(map(lambda user: user.login, get_users())) or chatter_name == get_user_by_ip(addr):
            return localize("CHAT_ADD_INVALID_NAME", addr=addr)

        if chatter_name in get_user_friends(addr):
            return localize("CHAT_ADD_ALREADY", addr=addr)

        db_sess = db_session.create_session()



        # APPENDING TO SENDER
        user = db_sess.query(__all_models.Users).get(get_user_by_ip(addr))
        friends = eval(user.friends)
        friends.append(str(chatter_name))
        user.friends = str(friends)

        # APPENDING TO CHATTER
        user = db_sess.query(__all_models.Users).get(chatter_name)
        friends = eval(user.friends)
        friends.append(str(get_user_by_ip(addr)))
        user.friends = str(friends)

        db_sess.commit()

        return localize("CHAT_ADD_SUCCESS", addr=addr, args=[chatter_name])



    if chatter_name not in get_user_friends(addr):
        return localize("CHAT_REMOVE_INVALID_NAME", addr=addr, args=[chatter_name])


    db_sess = db_session.create_session()

    # REMOVING FROM SENDER
    user = db_sess.query(__all_models.Users).get(get_user_by_ip(addr))
    friends = get_user_friends(addr)
    friends.remove(str(chatter_name))
    user.friends = str(friends)

    # REMOVING FROM CHATTER
    user = db_sess.query(__all_models.Users).get(chatter_name)
    friends = eval(user.friends)
    friends.remove(str(get_user_by_ip(addr)))
    user.friends = str(friends)

    db_sess.commit()

    return localize("CHAT_REMOVE_SUCCESS", addr=addr, args=[chatter_name])


if __name__ == '__main__':
    pass
