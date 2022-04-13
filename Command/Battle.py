import logging
import app
from data import __all_models, db_session
import json

log = logging.getLogger()


def get_battle_stats(key, username):
    """
    Функция выводит боевые статы [username]'а по ключу [key]
    Ключи:
        dmgM - урон в ближнем бою
        dmgR - урон от огнестрела
        prc - piercing - пробивание
        eng - сколько осталось энергии

    :param key: ключ
    :param username: имя пользователя
    """
    pass


def enter(username, battle_id):
    pass


def leave(username):
    pass


def attack(username):
    pass


def defend(username):
    pass


def heal(username):
    pass