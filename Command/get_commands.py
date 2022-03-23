from data import db_session, __all_models


def get_all_commands():
    command_list = []

    db_session.global_init("../db/main.db")


    db_sess = db_session.create_session()
    for value in db_sess.query(__all_models.Commands).all():
        command_list.append((value.name, value.syntax, value.description, value.python_func))

    return command_list


if __name__ == "__main__":
    print(get_all_commands())