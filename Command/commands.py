import json
import logging
from data import __all_models, db_session

log = logging.getLogger()
new_username = ""


# ======== COMMANDS GLOBAL FUNCS ========
def get_all_commands():
    command_list = []

    # log.debug("Opening db session for GETTING ALL COMMANDS")
    db_sess = db_session.create_session()
    for value in db_sess.query(__all_models.Commands).all():
        command_list.append((value.name, value.syntax, value.description, value.python_func))

    return command_list


def process_command(username, text):
    # Importing LOG from app.py
    global new_username
    import app
    global log
    log = app.log

    username = new_username = decode_name(username)

    all_commands = get_all_commands()
    command, *args = text.lower().split()

    for db_command in all_commands:
        if command == db_command[0]:
            log.debug(f"found command {command} in all commands list")
            args = [f"'{arg}'" for arg in args]

            log.debug(f"Executing {command} for {username}")
            return eval(f"{db_command[3]}('{username}', {', '.join(args)})"), encode_name(new_username)

    log.debug(f"Can't find {command} for {username}")
    return f"command \"{command}\" not found. Use help to get all commands", encode_name(new_username)


# ======== LOCALIZATION ========
special_symbols = {"~n": "\n", "~t": "\t"}
SELL_PRICE_DIVIDER = 1.2


def localize(code, username, args=None):
    if args is None:
        args = []

    from csv import reader

    args = list(map(str, args))

    lang = "EN"
    user = get_user(username)
    if user is not None:
        lang = user.lang

    # Reading csv file
    # log.debug("Opening and reading loc file")
    with open('csv/localizations.csv', encoding="utf8") as csvfile:
        reader = reader(csvfile, delimiter=';', quotechar='"')
        data = list(map(lambda x: x, reader))  # Storing data to list

    keys = {}
    for i, value in enumerate(data[0]):
        keys[value] = i  # getting keys dict {<header>: <ind>}
    phrases = data[1:]  # getting all phrases

    for line in phrases:  # going through all lines
        if code == line[0]:  # check if line.code == code
            # log.debug(f"Found {code} in loc.csv")

            output = str(line[keys[lang]])  # setting output

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
    with open('csv/localizations.csv') as csvfile:
        reader = reader(csvfile, delimiter=';', quotechar='"')
        data = list(map(lambda x: x, reader))  # Storing data to list

    keys = []
    for value in data[0][1:]:
        keys.append(str(value))

    # log.debug(f"Returning all langs: {keys}")
    return keys


def encode_name(username):
    user = get_user(username)

    if user is None:
        return username

    username_crypt = user.encoded_login

    return username_crypt.decode("utf-8")


def decode_name(username_crypt):
    if username_crypt is None:
        username_crypt = "!!"

    user = db_session.create_session().query(__all_models.Users).filter_by(
        encoded_login=username_crypt.encode("utf-8")).first()

    if user is None:
        user = db_session.create_session().query(__all_models.Users).filter_by(
            login=username_crypt).first()
        if user is None:
            return username_crypt

        return "Guest " + username_crypt

    username = user.login

    return username


# ======== LOGIN AND USERS ========
def get_user_friends(username):
    user = get_user(username)

    if user is None:
        return []

    if user and user.friends:
        log.debug(f"Found friends for {username}. Friends: {eval(user.friends)}")
        return eval(user.friends)

    return []


def get_users():
    # log.debug("(One action) Getting all users. Accessing main.db . Returning all users")
    return list(map(lambda user: user, db_session.create_session().query(__all_models.Users).all()))


def get_all_users_params():  # Delete
    log.debug("(One action) Getting all user params. Accessing main.db . Returning all user params")
    return list(map(lambda user_p: user_p, db_session.create_session().query(__all_models.UsersParams).all()))


def get_user(username):
    return db_session.create_session().query(__all_models.Users).get(username)


def get_user_params(username):
    log.debug(f"Getting {username} params")
    for user_p in get_all_users_params():
        if user_p.name == username:
            log.debug(f"Params for {username} found")

            return json.loads(user_p.stats)

    log.debug(f"Can't find params for user {username}")
    return None


def edit_user_stats(key, value, operation="+", username=""):
    # operation
    # + add, = set, * mul

    # log.debug(f"Getting user params for {username}")
    stats = get_user_params(username)

    # log.debug(f"Applying '{operation}{value}' operation for {key} param for {username}")
    if operation == "+":
        stats[key] += value
    elif operation == "-":
        stats[key] -= value
    elif operation == "*":
        stats[key] *= value
    elif operation == "=":
        stats[key] = value

    # log.debug("Opening main.db session")
    db_sess = db_session.create_session()

    # log.debug(f"Getting user params by name {username}")
    user_params = db_sess.query(__all_models.UsersParams).get(username)
    # log.debug(f"Editing {username} params to '{stats}'")
    user_params.stats = json.dumps(stats)

    # log.debug(f"Appending data to main.db for user {username}")
    db_sess.add(user_params)
    # log.debug("Closing main.db")
    db_sess.commit()


def send_user_password(username):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    import os
    from dotenv import load_dotenv
    from cryptography.fernet import Fernet

    log.debug(f"Recovering password for {username}")

    user = get_user(username)

    message = f'''
    Hello. 
    You have requested password recovery from account {user.login} in the Lambda-14 game. 
    Your password: {Fernet(user.personal_key).decrypt(user.password).decode('utf-8')}
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
    except Exception:
        return localize("PASSWORD_RECOVERY_EMAIL_NOT_VALID", username, args=[user.email])

    return localize("PASSWORD_RECOVERY_SUCCESS_SEND_MAIL", username, args=[user.email])


def command_password_recovery(username, *args):
    log.debug(f"[Command password recovery {username}] Executing")

    user = get_user(username)

    if user is None:
        log.debug(f"[Password Recovery {username}] Can't find user")
        return localize("PASSWORD_RECOVERY_NO_USER_IN_DB", username, args=[username])

    if not user.email:
        log.debug(f"[Password Recovery {username}] No email for {username} user")
        return localize("PASSWORD_RECOVERY_NO_USER_EMAIL", username, args=[username])

    log.debug(f"[Password Recovery {username}] Sending email with {username} user")
    return send_user_password(username)


# ======== CONSOLE COMMANDS ========
def command_help(username, *args):
    log.debug(f"[Command help {username}] Executing")

    return_data = localize("HELP_HEADER", username)

    log.debug(f"[Command help {username}] Getting all commands")
    for command in get_all_commands():
        description = localize(command[2], username)
        return_data += localize("HELP_FORMAT", username, args=[command[0], command[1], description])

    log.debug(f"[Command help {username}] Returning data")
    return return_data


def command_debug(username, *args):
    from datetime import datetime

    log.debug(f"[Command debug {username}] Executing")

    return_data = f"sender name \t {username}\n"
    return_data += f"server time \t {datetime.now()}\n"
    return_data += f"user \t {get_user(username).login if get_user(username) else 'user not found'}"

    return return_data


def command_clear(username, *args):
    log.debug(f"[Command clear {username}] Executing")

    return "!!clear"


def command_lang(username, *args):
    # log.debug(f"[Command lang {username}] Executing")

    if username not in list(map(lambda x: x.login, get_users())):
        # log.debug(f"[Command lang {username}] Can't find user")
        return f"Invalid user"

    all_langs = map(lambda x: x.lower(), get_all_langs())

    if len(args) < 1:
        # log.debug(f"[Command lang {username}] No lang provided")
        return localize("LANG_NO_LANG", username, args=[", ".join(all_langs)])
    lang = args[0]

    if lang not in all_langs:
        # log.debug(f"[Command lang {username}] Can't find '{lang}' lang")
        return localize("LANG_INCORRECT", username, args=[lang])

    # log.debug(f"[Command lang {username}] Opening main.db")
    db_sess = db_session.create_session()
    # log.debug(f"[Command lang {username}] Getting user")
    user = db_sess.query(__all_models.Users).get(username).first()
    # log.debug(f"[Command lang {username}] Setting lang")
    user.lang = lang.upper()
    # log.debug(f"[Command lang {username}] Commiting to main.db")
    db_sess.commit()

    return localize("LANG_SUCCESS", username, args=[lang])


def command_status(username, *args):
    # log.debug(f"[Command status {username}] Executing")
    target_name = username
    if len(args) >= 1:
        target_name = args[0]

    # log.debug(f"[Command status {username}] Getting params for {username}")
    target_params = get_user_params(target_name)

    if target_params is None:
        log.debug(f"[Command status {username}] Cant find {target_name} user in params table")
        return localize("STATUS_NO_USER_IN_BD", username, args=[username])

    return_data = [f"======== {target_name} stats ========"]
    for key, val in target_params.items():
        return_data.append(f'{key}: {val}')

    target_equip = get_user_equip(target_name)
    return_data.append(f"======== {target_name} equipment ========")
    for key, val in target_equip.items():
        if type(val) == dict:
            return_data.append(f"{key}")
            for k, v in val.items():
                return_data.append(f"\t{k}: {localize(v, username)}")
        elif type(val) == list:
            return_data.append(f"{key}: {val[0]} of {localize(val[1], username)}")
        else:
            return_data.append(f'{key}: {localize(val, username)}')

    # log.debug(f"[Command status {username}] Returning user params")
    return '\n'.join(return_data)


def command_wiki(username, *args):
    # log.debug(f"[Command wiki {username}] Executing")
    if len(args) == 0:
        log.debug(f"[Command wiki {username}] No argument provided")
        return localize("WIKI_HELP", username)

    category = args[0]

    if category == "all":
        # log.debug(f"[Command wiki {username}] Requesting all wikis")
        return wiki_material(username) + wiki_heal(username) + \
               wiki_armor(username) + wiki_melee(username) + wiki_range(username)

    # log.debug(f"[Command wiki {username}] Requesting {category} wiki")
    if category == "armor":
        return wiki_armor(username)
    if category == "heal":
        return wiki_heal(username)
    if category == "material":
        return wiki_material(username)
    if category == "melee":
        return wiki_melee(username)
    if category == "range":
        return wiki_range(username)

    # log.debug(f"[Command wiki {username}] Can't find {category} category")
    return localize("WIKI_INCORRECT_CATEGORY", username)


def command_inv(username, *args):
    log.debug(f"[Command inv {username}] Executing")

    log.debug(f"[Command inv {username}] Requesting inventory")
    inventory = get_items_by_user(username)

    output_text = "======== INVENTORY ========\nname \t count\n"
    for item in inventory:
        output_text += f"{localize(item[2], username)} \t {item[0]}\n"

    log.debug(f"[Command inv {username}] Returning items")
    return output_text


def command_login(username, *args):
    global new_username
    from cryptography.fernet import Fernet

    log.debug(f"[Command login {username}] Executing")

    if len(args) >= 1:
        username = args[0]
    else:
        log.debug(f"[Command login {username}] No username provided")
        return localize('LOGIN_NO_NAME', username)

    if len(args) >= 2:
        password = args[1]
    else:
        log.debug(f"[Command login {username}] No password provided")
        return localize('LOGIN_NO_PASSWORD', username)

    if username not in ["n.e.o.n", "lyagva"]:
        if len(args) >= 3:
            return localize("LOGIN_INCORRECT_TYPE", username)

        if list(filter(lambda x: x not in 'abcdefghijklmnopqrstuvwxyz0123456789-_', username)):
            return localize("LOGIN_INCORRECT_TYPE", username)

        if username in ["self", "guest", "global"]:
            return localize("LOGIN_INCORRECT_NAME", username)
    else:
        if username == "n.e.o.n":
            username = "N.E.O.N"
        elif username == "lyagva":
            username = "Lyagva"

    user = get_user(username)

    if user is not None:
        if Fernet(user.personal_key).decrypt(user.password).decode('utf-8') != password:
            log.debug(f"[Command login {username}] Incorrect password {password}")
            return localize('LOGIN_INCORRECT_PASSWORD', username, args=[username])
        else:
            new_username = username

            log.debug(f"[Command login {username}] Logged successfully")

            return localize('LOGIN_SUCCESS', username, args=[username])

    # ======== REGISTRATION ========
    key = Fernet.generate_key()

    user = __all_models.Users()
    user.login = new_username = username
    user.encoded_login = Fernet(key).encrypt(bytes(user.login, 'utf-8'))
    user.personal_key = key
    user.password = Fernet(key).encrypt(bytes(password, 'utf-8'))

    # Params
    user_params = __all_models.UsersParams()
    user_params.name = username

    # Dumping to DB
    db_sess = db_session.create_session()

    db_sess.add(user)
    db_sess.add(user_params)
    db_sess.commit()

    return localize('LOGIN_NEW_ACC_SUCCESS', username, args=[username])


def command_email(username, *args):
    if len(args) < 1:
        return localize("EMAIL_NO_FOUND", username)

    if username is None or get_user(username) is None:
        return localize("EMAIL_NO_LOGGED", username)

    email = args[0]
    db_sess = db_session.create_session()
    user = get_user(username)
    user.email = email

    db_sess.commit()
    return localize("EMAIL_ADD_SUCCESS", username, args=[email, username])


# ======== SHOP ========
def get_shop_items():
    log.debug(f"Getting shop items")
    return list(map(lambda category: {category: list(
        map(lambda item: item, db_session.create_session().query(eval('__all_models.' + category)).all()))},
                    ['ItemMaterial', 'ItemHeal', 'ItemArmor', 'ItemMeleeWeapon', 'ItemRangeWeapon']))


def command_buy(username, *args):
    log.debug(f"[Command buy {username}] Executing")
    if len(args) < 1:
        log.debug(f"[Command buy {username}] No item provided")
        return localize("BUY_NO_ITEM_PROVIDED", username)

    item_name = " ".join(args[:len(args) - 1])

    if len(args) > 1:
        if args[-1].isnumeric():
            count = int(args[-1])
        else:
            return localize("BUY_INVALID_COUNT", username)
    else:
        count = 1

    log.debug(f"[Command buy {username}] Getting all items")
    lst = get_shop_items()

    for i in lst:
        for category, items in i.items():
            for item in items:
                if item_name == localize(item.name, username).lower():

                    user_money = get_user_params(username)['money']

                    if user_money < item.price:
                        return localize("BUY_NO_MONEY", username)

                    while item.price * count > user_money:
                        count -= 1

                    cost = item.price * count

                    edit_user_stats("money", cost, operation="-", username=username)

                    item_to_add = [count, category, vars(item)['name']]
                    add_item(item_to_add, username)  # [1, 'itemMaterial', 'ITEM_MATERIAL_DEBUG_NAME']

                    return localize("BUY_SUSSESS", username, args=[count, item_name, cost])

    return localize("BUY_NO_ITEM_FOUND", username, args=[item_name])


def command_sell(username, *args):
    if len(args) < 1:
        return localize("SELL_NO_ITEM_PROVIDED", username)

    item_name = " ".join(args[0:len(args) - 1])

    if len(args) > 1:
        if args[-1].isnumeric():
            count = int(args[-1])
        else:
            return localize("SELL_INVALID_COUNT", username)
    else:
        count = 1

    inventory = get_items_by_user(username)

    for item in inventory:
        if item_name == localize(item[2], username).lower():
            count = min(count, int(item[0]))

            item[0] = -count

            class_name = item[1][0].upper() + item[1][1:]
            price = list(filter(lambda x: x.name == item[2],
                                db_session.create_session().query(eval('__all_models.' + class_name))))[0].price

            cost = int(price * count // SELL_PRICE_DIVIDER)

            edit_user_stats("money", cost, operation="+", username=username)

            add_item(item, username)  # добавляем в инвентарь отрицательное количество предмета

            return localize("SELL_SUCCESS", username, args=[count, item_name, cost])

    return localize("SELL_NO_ITEM_FOUND", username, args=[item_name])


# ======== WIKI ========
def wiki_armor(username):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemArmor).all()))
    output_text = ""

    # ARMOR
    output_text += "======== ARMOR ========\n"
    output_text += "name \t description \t price buy/sell \t slot \t defence \n"
    for item in items:
        info = [localize(item.name, username), localize(item.description, username),
                f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}', item.slot, item.defence]
        output_text += localize("WIKI_ARMOR_FORMAT", username, args=info) + "\n"

    return output_text


def wiki_heal(username):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemHeal).all()))
    output_text = ""

    # HEAL
    output_text += "======== HEAL ========\n"
    output_text += "name \t description \t price buy/sell \t heal amount \n"
    for item in items:
        info = [localize(item.name, username), localize(item.description, username),
                f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}', item.healAmount]
        output_text += localize("WIKI_HEAL_FORMAT", username, args=info) + "\n"

    return output_text


def wiki_material(username):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemMaterial).all()))
    output_text = ""

    # MATERIAL
    output_text += "======== MATERIAL ========\n"
    output_text += "name \t description \t price buy/sell \n"
    for item in items:
        info = [localize(item.name, username), localize(item.description, username),
                f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}']
        output_text += localize("WIKI_MATERIAL_FORMAT", username, args=info) + "\n"

    return output_text


def wiki_melee(username):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemMeleeWeapon).all()))
    output_text = ""

    # MELEE
    output_text += "======== MELEE WEAPON ========\n"
    output_text += "name \t description \t price buy/sell \t energy cost \t damage \t piercing \n"
    for item in items:
        info = [localize(item.name, username), localize(item.description, username),
                f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}',
                item.energyCost, item.damage, item.piercing]
        output_text += localize("WIKI_MELEE_FORMAT", username, args=info) + "\n"

    return output_text


def wiki_range(username):
    items = list(map(lambda user: user, db_session.create_session().query(__all_models.ItemRangeWeapon).all()))
    output_text = ""

    # RANGE
    output_text += "======== RANGE WEAPON ========\n"
    output_text += "name \t description \t price buy/sell \t energy cost \t damage \t piercing \t hit chance \n"
    for item in items:
        info = [localize(item.name, username), localize(item.description, username),
                f'{item.price}/{int(item.price // SELL_PRICE_DIVIDER)}',
                item.energyCost, item.damage, item.piercing, item.hitChance]
        output_text += localize("WIKI_RANGE_FORMAT", username, args=info) + "\n"

    return output_text


# ======== Inventory ========
def get_items_by_user(username=""):
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


def add_item(item, username=""):
    # Item
    # [count, table, name]
    db_sess = db_session.create_session()

    # Getting params
    if username not in list(map(lambda x: x.name, get_all_users_params())):
        userParams = __all_models.UsersParams()
    else:
        userParams = db_sess.query(__all_models.UsersParams).get(username)

    # Getting inventory
    inventory = get_items_by_user(username=username)

    print(item)
    # Check if item already in inventory
    for index, invItem in enumerate(inventory):
        print(invItem)
        if item[2] == invItem[2] or item[2] == localize(invItem[2], username):
            invItem[0] += item[0]
            if invItem[0] <= 0:
                inventory.pop(index)
            else:
                inventory[index] = invItem

            userParams.items = json.dumps({"items": inventory})
            db_sess.commit()
            return

    inventory.append(item)
    userParams.items = json.dumps({"items": inventory})
    db_sess.commit()


# ======== Chat ========
def command_chat(username, *args):
    if len(args) == 0:
        return localize("CHAT_NO_FUNC", username)
    func = args[0]

    if func not in ["add", "remove"]:
        return localize("CHAT_INVALID_FUNC", username)

    if len(args) <= 1:
        return localize("CHAT_NO_NAME", username)
    chatter_name = args[1]

    if func == "add":
        if chatter_name not in list(map(lambda x: x.login, get_users())) or chatter_name == username:
            return localize("CHAT_ADD_INVALID_NAME", username)

        if chatter_name in get_user_friends(username):
            return localize("CHAT_ADD_ALREADY", username)

        db_sess = db_session.create_session()

        # APPENDING TO SENDER
        print(username)
        user = db_sess.query(__all_models.Users).get(username)
        friends = eval(user.friends)
        friends.append(str(chatter_name))
        user.friends = str(friends)

        # APPENDING TO CHATTER
        user = db_sess.query(__all_models.Users).get(chatter_name)
        friends = eval(user.friends)
        friends.append(str(username))
        user.friends = str(friends)

        db_sess.commit()

        return localize("CHAT_ADD_SUCCESS", username)

    if chatter_name not in get_user_friends(username):
        return localize("CHAT_REMOVE_INVALID_NAME", username)

    db_sess = db_session.create_session()

    # REMOVING FROM SENDER
    user = db_sess.query(__all_models.Users).get(username)
    friends = get_user_friends(username)
    friends.remove(str(chatter_name))
    user.friends = str(friends)

    # REMOVING FROM CHATTER
    user = db_sess.query(__all_models.Users).get(chatter_name)
    friends = eval(user.friends)
    friends.remove(str(username))
    user.friends = str(friends)

    db_sess.commit()

    return localize("CHAT_REMOVE_SUCCESS", username)


# ============= Battle ==============
def get_user_equip(username):
    return json.loads(db_session.create_session().query(__all_models.UsersParams).get(username).equipment)


def command_equip(username, *args):
    if not get_user(username):
        return localize("USER_NOT_FOUND", username)

    if len(args) < 1:
        return localize("EQUIP_NO_ITEM", username)

    item_name = " ".join(args).strip().capitalize()

    item_type = ''
    item_class = None
    item_strange_name = ''

    user_inv = get_items_by_user(username)
    shop_itm = get_shop_items()

    for dct in shop_itm:
        for key, val in dct.items():
            for item in val:
                if localize(item.name, username) == item_name:
                    if key not in ["ItemHeal", "ItemArmor", "ItemMeleeWeapon", "ItemRangeWeapon"]:
                        return localize("EQUIP_INCORRECT_TYPE", username, args=[key])
                    item_type = key
                    item_class = item
                    item_strange_name = item.name

    if item_class is None:
        return localize("EQUIP_NO_SUCH_ITEM", username)

    if not list(filter(lambda itm: localize(itm[2], username) == item_name, user_inv)):
        return localize("EQUIP_NO_IN_INV", username)

    user_equip = get_user_equip(username)
    if item_type == "ItemArmor":
        item_sub_type = item_class.slot

        for item in user_inv:
            if item_name == localize(item[2], username):
                if user_equip[item_type][item_sub_type] != '':
                    old_equip = user_equip[item_type][item_sub_type]

                    item = [1, item_type, old_equip]
                    add_item(item, username)

                    item = [-1, item_type, item_strange_name]
                    add_item(item, username)

                    user_equip[item_type][item_sub_type] = item_strange_name

                else:
                    user_equip[item_type][item_sub_type] = item_strange_name

                    item = [-1, item_type, item_strange_name]
                    add_item(item, username)

    elif item_type == "ItemHeal":  # equip[heal] = [count, name]
        for item in user_inv:
            if item_name == localize(item[2], username):

                if user_equip[item_type] != '':
                    if user_equip[item_type][1] == item_name:  # стакаем
                        user_equip[item_type][0] += item[0]
                    else:  # меняем
                        item_old = [user_equip[item_type][0], "ItemHeal", user_equip[item_type][1]]
                        add_item(item_old, username)

                        user_equip[item_type] = [item[0], item_strange_name]
                else:
                    user_equip[item_type] = [item[0], item_strange_name]

                item[0] = -item[0]
                add_item(item, username)

    else:
        if not user_equip[item_type] == '':
            old_equip = user_equip[item_type]
            for dct in shop_itm:
                for key, val in dct.items():
                    for item in val:
                        if localize(item.name, username) == old_equip:
                            item = [1, key, item.name]
                            add_item(item, username)

        user_equip[item_type] = item_strange_name

        for item in user_inv:
            if item_name == localize(item[2], username):
                item[0] = -1
                add_item(item, username)

    db_sess = db_session.create_session()
    user = db_sess.query(__all_models.UsersParams).get(username)
    user.equipment = json.dumps(user_equip)
    db_sess.commit()

    return localize("EQUIP_SUCCESS", username)


if __name__ == '__main__':
    pass
