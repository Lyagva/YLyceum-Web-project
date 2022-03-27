from data import __all_models, db_session

# ======== LOCALIZATION ========
special_symbols = {"~n": "\n", "~t": "\t"}

def localize(code, addr, args=[]):
    from csv import reader

    lang = "EN"
    username = find_user_by_ip(addr)
    if username is not None:
        for user in get_users():
            if user.login == username:
                lang = user.lang



    # Reading csv file
    with open('csv/localize_commands.csv', encoding="utf8") as csvfile:
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
def get_users():
    return list(map(lambda user: user, db_session.create_session().query(__all_models.Users).all()))


def get_user_params():
    return list(map(lambda user_p: user_p, db_session.create_session().query(__all_models.UsersParams).all()))


def find_user_by_ip(addr):
    for user in get_users():
        if user.ip == addr:
            return user.login
    return None


def find_user_params_by_name(name):
    for user_p in get_user_params():
        if user_p.name == name:
            import json

            return json.loads(user_p.parameters)
    return None


def clear_old_data_ip(addr):
    db_sess = db_session.create_session()

    prev_user = find_user_by_ip(addr)
    if prev_user:
        prev_user = db_sess.query(__all_models.Users).get(prev_user)
        prev_user.ip = None

    db_sess.commit()


def command_login(addr, *args):
    if len(args) >= 1:
        username = args[0]
    else:
        return localize('LOGIN_NO_NAME', addr)

    if len(args) >= 2:
        password = args[1]
    else:
        return localize('LOGIN_NO_PASSWORD', addr)

    for user in get_users():
        if user.login != username:
            continue

        if not user.check_password(password):
            return localize('LOGIN_INCORRECT_PASSWORD', addr, args=[username])
        else:
            clear_old_data_ip(addr)

            db_sess = db_session.create_session()

            user = db_sess.query(__all_models.Users).get(user.login)

            user.ip = addr

            db_sess.commit()

            return localize('LOGIN_SUCCESS', addr, args=[username])

    clear_old_data_ip(addr)

    user = __all_models.Users()
    user.login = username
    user.set_password(password)
    user.ip = addr

    standart = {
                "hp": 100,  # базовое здоровье
                "energy": 5,  # базовое кол-во действий за ход
                "defence": 5,  # базовая защита
                "mattack": 5,  # базовый урон в ближнем бою
                "acc": 5,  # базовая точность %. 0.05 при расчётах
                "lvl": 1,  # уровень
                }

    user_params = __all_models.UsersParams()
    user_params.name = username
    user_params.ip = addr
    import json

    user_params.parameters = json.dumps(standart)

    db_sess = db_session.create_session()

    db_sess.add(user)
    db_sess.add(user_params)
    db_sess.commit()

    return localize('LOGIN_NEW_ACC_SUCCESS', addr, args=[username])



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
    print('WE ARE THERE')
    if len(args) < 1:
        return localize("STATUS_NO_USER", addr)

    username = args[0]

    user_params = find_user_params_by_name(username)

    if user_params is None:
        return localize("STATUS_NO_USER_IN_BD", addr)

    return_data = []
    for key, val in user_params.items():
        return_data.append(f'{key}: {val}')

    return '\n'.join(return_data)



if __name__ == '__main__':
    pass