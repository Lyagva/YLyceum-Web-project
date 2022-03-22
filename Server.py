from flask import Flask, render_template
import Logger

log = Logger.set_logging() #  Задаём логгер. Для логов надо писать log.<уровень>(<текст>)

app = Flask(__name__)
app.config["SECRET_CODE"] = "Very strange thing"



if __name__ == "__main__":
    log.info("Server Starting")
    app.run("", 5000)
