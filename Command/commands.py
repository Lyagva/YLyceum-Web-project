from data import __all_models, db_session
import json

# ======== LOCALIZATION ========
special_symbols = {"~n": "\n", "~t": "\t"}
SELL_PRICE_DIVIDER = 1.2


def localize(code, addr, args=[]):
    from csv import reader

    args = list(map(str, args))

    lang = "EN"
    username = find_user_by_ip(addr)
    if username is not None:
        for user in get_users():
            if user.login == username:
                lang = user.lang



    # Reading csv file
    with open('csv/localizations.csv', encoding="utf8") as csvfile:
        reader = reader(csvfile, delimiter=';', quotechar='"')
        data = list(map(lambda x: x, reader)) # Storing data to list

    keys = {}
    for i, value in enumerate(data[0]):
        keys[value] = i # getting keys dict {<header>: <ind>}
    phrases = data[1:] # getting all phrases

    for line in phrases: # going through all lines
        if code == line[0]: # check if line.code == code
            output = str(line[keys[lang]]) # setting output

            for key in special_symbols.keys():
                output = output.replace(key, special_symbols[key])

            for i in range(min(output.count("{}"), len(args))):
                output = output.replace("{}", args[i], 1)

            return output

    return "Phrase not found"


def get_all_langs():
    from csv import reader
    with open('csv/localize_commands.csv', encoding="utf8") as csvfile:
        reader = reader(csvfile, delimiter=';', quotechar='"')
        data = list(map(lambda x: x, reader)) # Storing data to list

    keys = []
    for value in data[0][1:]:
        keys.append(str(value))

    return keys


# ======== LOGIN AND USERS ========
def get_user_friends(addr):
    for user in get_users():
        if user.ip == addr and user.friends:
            return eval(user.friends)
    return []

def get_users():
    return list(map(lambda user: user, db_session.create_session().query(__all_models.Users).all()))


def get_user_params():
    return list(map(lambda user_p: user_p, db_session.create_session().query(__all_models.UsersParams).all()))


def find_user_by_ip(addr):
    for user in get_users():
        if user.ip == addr:
            return user.login
    return None


def find_ip_by_user(name):
    for user in get_users():
        if user.login == name:
            if user.ip:
                return user.ip
    return None


def find_user_params_by_name(name):
    for user_p in get_user_params():
        if user_p.name == name:
            import json

            return json.loads(user_p.stats)
    return None


def edit_user_stats(key, value, type="+", addr="", username=""):
    # type
    # + add, = set, * mul
    if addr:
        username = find_user_by_ip(addr)
    elif username == "":
        return

    stats = find_user_params_by_name(username)

    if type == "+":
        stats[key] += value
    elif type == "-":
        stats[key] -= value
    elif type == "*":
        stats[key] *= value
    elif type == "=":
        stats[key] = value


    db_sess = db_session.create_session()

    user_params = db_sess.query(__all_models.UsersParams).get(username)
    user_params.stats = json.dumps(stats)

    db_sess.add(user_params)
    db_sess.commit()


def clear_old_data_ip(addr):
    db_sess = db_session.create_session()

    prev_user = find_user_by_ip(addr)
    if prev_user:
        prev_user = db_sess.query(__all_models.Users).get(prev_user)
        prev_user.ip = None

    db_sess.commit()


def command_login(addr, *args):
    from cryptography.fernet import Fernet

    if len(args) >= 1:
        username = args[0]
    else:
        return localize('LOGIN_NO_NAME', addr)

    if len(args) >= 2:
        password = args[1]
    else:
        return localize('LOGIN_NO_PASSWORD', addr)

    if username in ["self"]:
        return localize("LOGIN_INCORRECT_NAME", addr)

    for user in get_users():
        if user.login != username:
            continue

        if Fernet(user.key_code_password).decrypt(user.password).decode('utf-8') != password:
            return localize('LOGIN_INCORRECT_PASSWORD', addr, args=[username])
        else:
            clear_old_data_ip(addr)

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

    username = find_user_by_ip(addr)
    if username is None:
        return localize("EMAIL_NO_LOGGED", addr)

    email = args[0]
    db_sess = db_session.create_session()
    for user in db_sess.query(__all_models.Users).all():
        if user.login == username:
            print('email SUCCESS')
            user.email = email
    db_sess.commit()
    return localize("EMAIL_ADD_SUCCESS", addr, args=[email, username])


def send_user_password(addr, user):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    import os
    from dotenv import load_dotenv
    from cryptography.fernet import Fernet

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
    if len(args) < 1:
        return localize("PASSWORD_RECOVERY_NO_USERNAME", addr)

    username = args[0]

    usr = None
    for user in get_users():
        if user.login == username:
            usr = user

    if usr is None:
        return localize("PASSWORD_RECOVERY_NO_USER_IN_DB", addr, args=[username])

    if not usr.email:
        return localize("PASSWORD_RECOVERY_NO_USER_EMAIL", addr, args=[username])

    return send_user_password(addr, usr)


# ======== CONSOLE COMMANDS ========
def command_help(addr, *args):
    from Command.get_commands import get_all_commands

    return_data = localize("HELP_HEADER", addr)

    for command in get_all_commands():
        description = localize(command[2], addr)
        return_data += localize("HELP_FORMAT", addr, args=[command[0], command[1], description])

    return return_data


def command_debug(addr, *args):
    from datetime import datetime
    return_data = f"sender address \t {addr}\n"
    return_data += f"server time \t {datetime.now()}\n"
    return_data += f"user \t {find_user_by_ip(addr) if find_user_by_ip(addr) else 'user not found'}"

    return return_data


def command_clear(addr, *args):
    return "!!clear"


def command_lang(addr, *args):
    all_langs = map(lambda x: x.lower(), get_all_langs())

    if len(args) < 1:
        return localize("LANG_NO_LANG", addr, args=[", ".join(all_langs)])
    lang = args[0]

    if lang not in all_langs:
        return localize("LANG_INCORRECT", addr, args=[lang])

    db_sess = db_session.create_session()
    user = db_sess.query(__all_models.Users).filter_by(ip=addr).first()
    user.lang = lang.upper()
    db_sess.commit()

    return localize("LANG_SUCCESS", addr, args=[lang])


def command_status(addr, *args):
    if len(args) < 1:
        return localize("STATUS_NO_USER", addr)

    username = args[0]
    if username == "self":
        username = find_user_by_ip(addr)

    user_params = find_user_params_by_name(username)

    if user_params is None:
        return localize("STATUS_NO_USER_IN_BD", addr, args=[username])

    return_data = []
    for key, val in user_params.items():
        return_data.append(f'{key}: {val}')

    return '\n'.join(return_data)


def command_wiki(addr, *args):
    if len(args) == 0:
        return localize("WIKI_HELP", addr)

    if args[0] == "all":
        return wiki_material(addr) + wiki_ammo(addr) + wiki_heal(addr) + \
               wiki_armor(addr) + wiki_melee(addr) + wiki_range(addr)

    if args[0] == "ammo":
        return wiki_ammo(addr)
    if args[0] == "armor":
        return wiki_armor(addr)
    if args[0] == "heal":
        return wiki_heal(addr)
    if args[0] == "material":
        return wiki_material(addr)
    if args[0] == "melee":
        return wiki_melee(addr)
    if args[0] == "range":
        return wiki_range(addr)

    return localize("WIKI_INCORRECT_CATEGORY", addr)


def command_inv(addr, *args):
    inventory = get_items_by_user(addr)


    outputText = "======== INVENTORY ========\nname \t count\n"
    for item in inventory:
        outputText += f"{localize(item[2], addr)} \t {item[0]}\n"

    return outputText


def get_shop_items(addr):
    return list(map(lambda category: {category: list(map(lambda item: item, db_session.create_session().query(eval('__all_models.' + category)).all()))}, ['ItemMaterial', 'ItemHeal', 'ItemArmor', 'ItemMeleeWeapon', 'ItemRangeWeapon', 'ItemAmmo']))


#     =================== SHOP ===========================
def command_buy(addr, *args):
    if len(args) < 1:
        return localize("BUY_NO_ITEM_PROVIDED", addr)

    item_name = " ".join(args[:len(args) - 1])

    if len(args) > 1:
        if args[-1].isnumeric():
            count = int(args[-1])
        else:
            return localize("BUY_INVALID_COUNT", addr)
    else:
        count = 1

    lst = get_shop_items(addr)

    for i in lst:
        for category, items in i.items():
            for item in items:
                if item_name == localize(item.name, addr).lower():

                    user_money = find_user_params_by_name(find_user_by_ip(addr))['money']

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
        username = find_user_by_ip(addr)
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

    print(inventory, inventory.items)
    return json.loads(inventory.items)["items"]


def add_item_by_ip(item, addr="", username=""):
    # Item
    # [count, durability, table, name]

    if addr != "":
        username = find_user_by_ip(addr)
    elif username == "":
        return "No user provided"

    db_sess = db_session.create_session()

    # Getting params
    if username not in list(map(lambda x: x.name, get_user_params())):
        userParams = __all_models.UsersParams()
    else:
        userParams = db_sess.query(__all_models.UsersParams).get(username)

    # Getting inventory
    inventory = get_items_by_user(username=username)

    # Check if item already in inventory
    print(inventory)
    print(item)
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


if __name__ == '__main__':
    pass
