from flask import Flask, render_template
from flask_socketio import SocketIO
import Logger

log = Logger.set_logging() #  Задаём логгер. Для логов надо писать log.<уровень>(<текст>)

app = Flask(__name__)
app.config["SECRET_CODE"] = "Very strange thing"
socketio = SocketIO(app) #  Задаём сервер с системой socket



if __name__ == "__main__":
    log.info("Server Starting")
    socketio.run(app) #  Запускаем сокет-сервер