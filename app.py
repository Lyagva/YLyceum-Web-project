import os

from flask import Flask, render_template, json, request, make_response, jsonify
from flask_restful import Api, Resource

from Command.commands import *
from Logger import set_logger
from data import db_session

start_msg = """"""

app = Flask(__name__)

log = set_logger()

console_outputs = {}

user_chats_opened = {}
user_chats_outputs = {"global": []}  # [name1, name2]: outputs


api = Api(app)


class RestApi(Resource):
    def get(self, username, type_info):
        if type_info == "status":
            return self.get_statistic(username)
        elif type_info == "inventory":
            return self.get_inventory(username)

    @staticmethod
    def get_statistic(username):
        return jsonify({"data": command_status(username)})

    @staticmethod
    def get_inventory(username):
        return jsonify({"data": command_inv(username)})


api.add_resource(RestApi, '/api/v2/<string:username>/<string:type_info>')


@app.route("/")
def index():
    # log.debug("Returning INDEX template for" + request.remote_addr)
    return render_template("index.html")


@app.route("/chat/<name>", methods=["GET", "POST"])
def index2(name):
    username = request.cookies.get("username")
    if request.method == "POST":
        if username == "null" or username is None:
            username = request.form["username"]
    username = decode_name(username)

    chat_name = "-".join(sorted([username, name])) if name != "global" else "global"

    user_chats_opened[username] = chat_name

    user_friends = get_user_friends(username)

    return render_template("index2.html", user_friends=user_friends)


@app.route("/sendDataChat", methods=["GET", "POST"])
def chat():
    username = request.cookies.get("username")
    if username == "null" or username is None:
        username = request.form["username"]
    sender = username = decode_name(username)

    update = True if request.form["update"] == "true" else False

    if username not in user_chats_opened.keys():
        user_chats_opened[username] = "global"

    chat_name = user_chats_opened[username]

    if not update:
        textIn = request.form["commandInput"]
        user_chats_outputs[chat_name].append(f"{sender} >>> {textIn}")

    if chat_name not in user_chats_outputs.keys():
        user_chats_outputs[chat_name] = []
    current_chat = user_chats_outputs[chat_name]

    return_data = {"outputs": current_chat, "username": username}
    return json.dumps(return_data)


@app.route("/sendData", methods=["GET", "POST"])
def post():
    username = request.cookies.get("username")
    if username == "null" or username is None:
        username = request.form["username"]
    new_username = username


    update = True if request.form["update"] == "true" else False

    if username not in console_outputs:
        console_outputs[username] = [start_msg]


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
    resp = make_response(json.dumps({"outputs": console_outputs[username],
                                     "clearChild": clear_child,
                                     "username": new_username}))
    resp.set_cookie('username', new_username)
    return resp


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    # log.info("Opening db/main.db")
    db_session.global_init("db/main.db")


    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
