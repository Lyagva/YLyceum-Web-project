import logging
import os
import sys
from datetime import datetime


def set_logging():
    """
    Функция, создающая и возвращающая логгер. Логгер - объект, нужный для вывода и записи данных в консоль/файл.
    Все сетевые выводы кроме выводов из разряда: "А какой тип данных оно выводит?", рекомендую делать через логи.

    Использование:
        log = set_logging() # Пишется в начале
        log.<уровень>(<сообщение>)

    Уровни:
        debug - для отладочных сообщений (почти не используется)
        info - для обычных сообщений
        warning - для предупреждений. К примеру: "мало места на диске"
        error - для ошибок (обычно без вылета всей программы).
                К примеру: "потерян пакет" или "не удалось получить данные из бд"
        critical - для фатальных ошибок и краше. К примеру: "нет подключения к сети"


    Пример использования:
        log.debug("Получен пакет данных")
        log.info("Всё в порядке")
        log.warning("Плохое интернет соединение")
        log.error("Не удалось отправить пакет")
        log.critical("Комп умер от синего экрана смерти")

    :return:
    """

    if not os.path.exists(os.path.abspath("./logs")): #  Проверяем есть ли директория для логов
        os.makedirs("./logs") #  Создаём директорию для логов

    formatter = logging.Formatter('%(levelname)s - %(asctime)s >>> %(message)s') #  Формат сообщения в логах
    time = datetime.now().strftime("%d-%m-%y--%H-%M-%S") #  Формат времени в имени файла

    logger = logging.getLogger() #  Создание главного логгера
    logger.setLevel("INFO")

    fileHandler = logging.FileHandler(filename=f"logs/log{time}.log") #  Логгера для файлов + указание имени файла
    fileHandler.setFormatter(formatter) #  Изменение формата записи в файл
    logger.addHandler(fileHandler) #  Добавление логгера файла в главный логгер

    streamHandler = logging.StreamHandler(sys.stdout) #  Логгер для вывода в консоль
    streamHandler.setFormatter(formatter) #  Изменение формата вывода в консоль
    logger.addHandler(streamHandler) #  Добавление логгера консоли в главный логгер


    logger.info("Logger is ready!") #  Проверка работы логгера

    return logger