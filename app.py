import datetime
from flask import Flask, render_template, json, request
import Logger
from Command.parse_command import parse_command


app = Flask(__name__)
log = Logger.set_logging()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sendData", methods=["GET", "POST"])
def post():

    outputText = parse_command(request.remote_addr, request.form["commandInput"])

    return json.dumps({"outputText": outputText})

@app.route("/update", methods=["GET", "POST"])
def update():
    return ""


if __name__ == "__main__":
    app.run()