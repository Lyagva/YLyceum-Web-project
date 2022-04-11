import os
from flask import Flask, render_template, json, request, redirect
from Logger import set_logger
from Command.commands import *
from data import db_session

app = Flask(__name__)
log = set_logger()

console_outputs = {}

user_chats_opened = {}  # ip: name_of_chat
user_chats_outputs = {"global": []}  # [name1, name2]: outputs


@app.route("/")
def index():
    # log.debug("Returning INDEX template for" + request.remote_addr)
    return render_template("index.html")


@app.route("/chat/<name>")
def index2(name):
    from Command.commands import get_user_friends

    addr = request.remote_addr

    # log.debug("Trying to get friends for", addr)
    user_friends = get_user_friends(addr)

    if name not in ["global", *user_friends]:
        # log.debug("Returning 404 template for" + addr)
        return page_not_found('404')

    # log.debug(f"Adding {addr} chat with name {name}")
    user_chats_opened[addr] = name

    # log.debug("Returning INDEX2 template for" + addr)
    return render_template("index2.html", user_friends=user_friends)


@app.route("/sendDataChat", methods=["GET", "POST"])
def chat():
    addr = request.remote_addr
    name_from = request.form["username"]

    # Name To
    name_to = "global"
    try:
        log.debug(f"Trying to get chat by {addr}")
        name_to = user_chats_opened[addr]
    except KeyError:
        redirect("global")

    # Making cool name
    if name_from is None:
        # log.debug("Making cool name for guest")
        name_from = f"Guest {'.'.join(addr.split('.')[:3])}.###"

    if request.method == "POST":
        textIn = request.form["commandInput"]
        if textIn:
            if name_to == "global":
                # log.debug(f"Appending message to {name_to} chat with text {textIn}")
                user_chats_outputs["global"].append(f"[{name_from}] >>>>>> {textIn}")
            else:
                chat_name_from = f"{name_from}-{name_to}"
                if chat_name_from not in user_chats_outputs.keys():
                    # log.debug(f"Creating chat {name_to}")
                    user_chats_outputs[chat_name_from] = []

                # log.debug(f"Appending message to {chat_name_from} chat with text {textIn}")
                user_chats_outputs[chat_name_from].append(f"[{name_from}] >>>>>> {textIn}")

                chat_name_to = f"{name_to}-{name_from}"
                if chat_name_to not in user_chats_outputs.keys():
                    # log.debug(f"Creating chat {chat_name_to}")
                    user_chats_outputs[chat_name_to] = []

                # log.debug(f"Appending message to {chat_name_to} chat with text {textIn}")
                user_chats_outputs[chat_name_to].append(f"[{name_from}] >>>>>> {textIn}")

        chat_name_from = f"{name_from}-{name_to}"
        return "Shit"


    if request.method == "GET":
        chat_name_from = f"{name_from}-{name_to}"
        if name_to == "global":
            chat_name_from = name_to

        # log.debug(f"Returning {name_from} chat data")
        return json.dumps({"outputs": user_chats_outputs[chat_name_from]})

    return "Secret achievement"


@app.route("/sendData", methods=["GET", "POST"])
def post():
    username = request.form["username"]
    update = True if request.form["update"] == "true" else False

    if username not in console_outputs:
        console_outputs[username] = []


    if update:
        # log.debug(f"Returning console outputs for {addr}")
        return json.dumps({"outputs": console_outputs[username], "clearChild": False})

    textIn = request.form["commandInput"]

    if len(textIn) == 0:
        # log.debug(f"No text provided. Returning console outputs for {addr}")
        return json.dumps({"outputs": console_outputs[username], "clearChild": False})

    # log.debug(f"Operating with command {textIn} from {addr}")
    textOut = process_command(username, textIn)

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
    return json.dumps({"outputs": console_outputs[username], "clearChild": clear_child})


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    # log.info("Opening db/main.db")
    db_session.global_init("db/main.db")


    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
