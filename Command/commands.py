from data import __all_models, db_session


def command_help(addr, *args):
    from Command.get_commands import get_all_commands

    return_data = "name \t syntax \t description\n"

    for command in get_all_commands():
        return_data += f"{command[0]} \t {command[1]} \t {command[2]}\n"

    return return_data


def command_debug(addr, *args):
    from datetime import datetime
    return_data = f"sender address \t {addr}\n"
    return_data += f"server time \t {datetime.now()}"

    return return_data


def get_users():
    return list(map(lambda user: user, db_session.create_session().query(__all_models.Users).all()))


def command_login(addr, *args):
    try:
        user_name, password = args[:2]
    except ValueError:
        return "Syntax error!!!"

    for user in get_users():
        if user.login != user_name:
            continue

        if not user.check_password(password):
            return 'The name is busy or the password is incorrect'

        elif user.check_password(password):
            # добавление пользователя в словарь с ip
            return 'You have successfully logged in to your account'

    user = __all_models.Users()
    user.login = user_name
    user.set_password(password)
    db_sess = db_session.create_session()
    db_sess.add(user)
    db_sess.commit()
    # + добавление пользователя в словарь с ip
    return 'You have successfully created a new account'
