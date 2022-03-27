from data import __all_models, db_session


def get_locale_command(code, lang='EN'):
    import csv

    abbreav = {}
    with open('../csv/localize_commands.csv', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        lst = list(map(lambda x: x, reader))

    for i, abb in enumerate(lst[0]):
        abbreav[abb] = i

    if lang not in abbreav.keys():
        return "Unsupported lang"

    for line in lst[1:]:
        if code in line:
            return line[abbreav[lang]]

    return "Phrase not found"

# ======== LOGIN AND USERS ========
def get_users():
    return list(map(lambda user: user, db_session.create_session().query(__all_models.Users).all()))


def find_user_by_ip(addr):
    for user in get_users():
        if user.ip == addr:
            return user.login
    return None


def command_login(addr, *args):
    if len(args) >= 1:
        user_name = args[0]
    else:
        return get_locale_command('NO_NAME', lang='EN')

    if len(args) >= 2:
        password = args[1]
    else:
        return get_locale_command('NO_PASSWORD', lang='EN')

    for user in get_users():
        if user.login != user_name:
            continue

        if not user.check_password(password):
            return get_locale_command('INCORRECT_PASSWORD', lang='EN')
        else:
            db_sess = db_session.create_session()

            prev_user = find_user_by_ip(addr)
            if prev_user:
                prev_user = db_sess.query(__all_models.Users).get(prev_user)
                prev_user.ip = None

            user = db_sess.query(__all_models.Users).get(user.login)
            user.ip = addr
            db_sess.commit()

            return get_locale_command('LOGIN_SUCCESS', lang='EN')

    user = __all_models.Users()
    user.login = user_name
    user.set_password(password)
    user.ip = addr
    db_sess = db_session.create_session()

    prev_user = find_user_by_ip(addr)
    if prev_user:
        prev_user = db_sess.query(__all_models.Users).get(prev_user)
        prev_user.ip = None

    db_sess.add(user)
    db_sess.commit()

    return get_locale_command('NEW_ACC_SUCCESS', lang='EN')



# ======== CONSOLE COMMANDS ========
def command_help(addr, *args):
    from Command.get_commands import get_all_commands

    return_data = "name \t syntax \t description\n"

    for command in get_all_commands():
        return_data += f"{command[0]} \t {command[1]} \t {command[2]}\n"

    return return_data


def command_debug(addr, *args):
    from datetime import datetime
    return_data = f"sender address \t {addr}\n"
    return_data += f"server time \t {datetime.now()}\n"
    return_data += f"user \t {find_user_by_ip(addr) if find_user_by_ip(addr) else 'user not found'}"

    return return_data


def command_clear(addr, *args):
    return "!!clear"


if __name__ == '__main__':
    print(get_locale_command('NO_NAME', lang='EN'))