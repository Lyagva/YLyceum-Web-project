import os

from flask import Flask, render_template, json, request
import Logger
from Command.parse_command import parse_command
from data import db_session

app = Flask(__name__)
log = Logger.set_logging()

console_outputs = {}
chat_outputs = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat")
def index2():
    return render_template("index2.html")


@app.route('/sendDataChat', methods=["GET", "POST"])
def chat():
    addr = request.remote_addr
    if request.method == "POST":
        from Command.commands import find_user_by_ip

        textIn = request.form["commandInput"]
        if textIn:
            username = find_user_by_ip(addr)
            if username is None:
                username = 'NoName'
            textOut = username + ':     ' + textIn
            chat_outputs.append(textOut)
    if request.method == "GET":
        return json.dumps({'outputs': chat_outputs})

    return json.dumps({'outputs': chat_outputs})


@app.route("/sendData", methods=["GET", "POST"])
def post():
    addr = request.remote_addr

    if addr not in console_outputs:
        console_outputs[addr] = []

    if request.method == "GET":
        return json.dumps({"outputs": console_outputs[addr]})


    textIn = request.form["commandInput"]

    if len(textIn) == 0:
        return json.dumps({"outputs": console_outputs[addr]})

    textOut = parse_command(addr, textIn)
    console_outputs[addr].append(f">>> {textIn}\n\n{textOut}")

    if textOut == "!!clear":  # Clear command
        console_outputs[addr] = []

    clear_child = False
    if len(console_outputs[addr]) > 5:
        clear_child = True
        console_outputs[addr] = console_outputs[addr][1:]


    return json.dumps({"outputs": console_outputs[addr], "clearChild": clear_child})


if __name__ == "__main__":
    db_session.global_init("db/main.db")

    # LOCALHOST
    # app.run()

    # HEROKU
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
