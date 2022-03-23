from data import db_session, __all_models


def get_all_armor():
    items_list = []

    db_session.global_init("../db/main.db")


    db_sess = db_session.create_session()
    for value in db_sess.query(__all_models.Armor).all():
        items_list.append((value.name, value.slot, value.description))

    return items_list


def get_all_melee():
    items_list = []

    db_session.global_init("../db/main.db")


    db_sess = db_session.create_session()
    for value in db_sess.query(__all_models.Melee).all():
        items_list.append((value.name, value.melee_type, value.description))

    return items_list


if __name__ == "__main__":
    print("======== ARMOR ========")
    print(get_all_armor())

    print("\n======== MELEE ========")
    print(get_all_melee())