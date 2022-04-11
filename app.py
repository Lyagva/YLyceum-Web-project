import os
from flask import Flask, render_template, json, request, redirect
from Logger import set_logger
from Command.commands import *
from data import db_session

app = Flask(__name__)
log = set_logger()

console_outputs = {}

user_chats_opened = {}
user_chats_outputs = {"global": []}  # [name1, name2]: outputs


@app.route("/")
def index():
    # log.debug("Returning INDEX template for" + request.remote_addr)
    return render_template("index.html")


@app.route("/chat/<name>")
def index2(name):
    username = sender = request.form["username"]
    chat_name = "-".join(sorted([username, name])) if name != "global" else "global"

    user_chats_opened[username] = chat_name

    user_friends = get_user_friends(username)

    return render_template("index2.html", user_friends=user_friends)


@app.route("/sendDataChat", methods=["GET", "POST"])
def chat():
    username = sender = request.form["username"]
    update = True if request.form["update"] == "true" else False
    textIn = request.form["commandInput"]

    if username not in user_chats_opened.keys():
        user_chats_opened[username] = "global"

    chat_name = user_chats_opened[username]

    if not update:
        user_chats_outputs[chat_name].append(f"{sender} >>> {textIn}")

    current_chat = user_chats_outputs[chat_name]

    return_data = {"ouputs": current_chat, "username": username}
    print(user_chats_opened)
    print(user_chats_outputs)
    return json.dumps(return_data)

@app.route("/sendData", methods=["GET", "POST"])
def post():
    username = new_username = request.form["username"]
    update = True if request.form["update"] == "true" else False

    if username not in console_outputs:
        console_outputs[username] = []


    if update:
        # log.debug(f"Returning console outputs for {addr}")
        return json.dumps({"outputs": console_outputs[username], "clearChild": False, "username": new_username})

    textIn = request.form["commandInput"]

    if len(textIn) == 0:
        # log.debug(f"No text provided. Returning console outputs for {addr}")
        return json.dumps({"outputs": console_outputs[username], "clearChild": False, "username": new_username})

    # log.debug(f"Operating with command {textIn} from {addr}")
    textOut, new_username = process_command(username, textIn)

    # log.debug(f"Appending text to {addr}'s console")
    console_outputs[username].append(f">>> {textIn}\n\n{textOut}")

    if textOut == "!!clear":
        # log.debug(f"Clearing console for {addr}")
        console_outputs[username] = []

    clear_child = len(console_outputs[username]) > 5
    if clear_child:
        # log.debug(f"Deleting old console data (5+ lines) for {addr}")
        console_outputs[username] = console_outputs[username][1:]

    # log.debug(f"Returning console outputs for {addr}")
    return json.dumps({"outputs": console_outputs[username], "clearChild": clear_child, "username": new_username})


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    # log.info("Opening db/main.db")
    db_session.global_init("db/main.db")


    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
