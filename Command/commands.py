from data import __all_models, db_session



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
        return "No username provided"

    if len(args) >= 2:
        password = args[1]
    else:
        return "No password provided"

    for user in get_users():
        if user.login != user_name:
            continue

        if not user.check_password(password):
            return 'The name is busy or the password is incorrect'
        else:
            db_sess = db_session.create_session()

            prev_user = find_user_by_ip(addr)
            if prev_user:
                prev_user = db_sess.query(__all_models.Users).get(prev_user)
                prev_user.ip = None

            user = db_sess.query(__all_models.Users).get(user.login)
            user.ip = addr
            db_sess.commit()

            return 'You successfully logged to your account'

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

    return 'You successfully created new account'



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
