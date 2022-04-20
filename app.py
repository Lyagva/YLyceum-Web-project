import os

from flask import Flask, render_template, json, request, make_response, jsonify
from flask_restful import Api, Resource

from Command.commands import *
from Logger import set_logger
from data import db_session

start_msg = """"""

app = Flask(__name__)

log = set_logger()

# console_outputs = {}
#
# user_chats_opened = {}
# user_chats_outputs = {"global": []}  # [name1, name2]: outputs


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

    dct = get_vars()
    dct["user_chats_opened"][username] = chat_name
    set_vars(dct)

    user_friends = get_user_friends(username)

    return render_template("index2.html", user_friends=user_friends)


@app.route("/sendDataChat", methods=["GET", "POST"])
def chat():
    username = request.cookies.get("username")
    if username == "null" or username is None:
        username = request.form["username"]
    sender = username = decode_name(username)

    update = True if request.form["update"] == "true" else False

    dct = get_vars()

    if username not in dct["user_chats_opened"].keys():
        dct["user_chats_opened"][username] = "global"

    chat_name = dct["user_chats_opened"][username]

    if not update:
        textIn = request.form["commandInput"]
        if textIn not in ["", " ", "  "]:
            dct["user_chats_outputs"][chat_name].append(f"{sender} >>> {textIn}")

    if chat_name not in dct["user_chats_outputs"].keys():
        dct["user_chats_outputs"][chat_name] = []
    current_chat = dct["user_chats_outputs"][chat_name]

    set_vars(dct)

    return_data = {"outputs": current_chat, "username": username}
    return json.dumps(return_data)


@app.route("/sendData", methods=["GET", "POST"])
def post():
    username = request.cookies.get("username")
    if username == "null" or username is None:
        username = request.form["username"]
    new_username = username

    dct = get_vars()
    set_vars(dct)

    update = True if request.form["update"] == "true" else False

    if username not in dct["console_outputs"]:
        dct["console_outputs"][username] = [start_msg]
        set_vars(dct)


    if update:
        # log.debug(f"Returning console outputs for {addr}")
        return json.dumps({"outputs": dct["console_outputs"][username], "clearChild": False, "username": new_username})

    textIn = request.form["commandInput"]

    if len(textIn) == 0:
        # log.debug(f"No text provided. Returning console outputs for {addr}")
        return json.dumps({"outputs": dct["console_outputs"][username], "clearChild": False, "username": new_username})

    # log.debug(f"Operating with command {textIn} from {addr}")
    textOut, new_username = process_command(username, textIn)
    dct = get_vars()

    # log.debug(f"Appending text to {addr}'s console")
    dct["console_outputs"][username].append(f">>> {textIn}\n\n{textOut}")
    set_vars(dct)

    if textOut == "!!clear":
        # log.debug(f"Clearing console for {addr}")
        dct["console_outputs"][username] = []
        set_vars(dct)

    clear_child = len(dct["console_outputs"][username]) > 5
    if clear_child:
        # log.debug(f"Deleting old console data (5+ lines) for {addr}")
        dct["console_outputs"][username] = dct["console_outputs"][username][1:]
        set_vars(dct)

    # log.debug(f"Returning console outputs for {addr}")
    resp = make_response(json.dumps({"outputs": dct["console_outputs"][username],
                                     "clearChild": clear_child,
                                     "username": new_username}))
    print(dct)
    resp.set_cookie('username', new_username)
    return resp


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def get_vars():
    with open("vars.json") as file:
        dct = json.loads(file.read())
    return dct


def set_vars(vars):
    with open("vars.json", "w+") as file:
        file.write(json.dumps(vars))


if __name__ == "__main__":
    # log.info("Opening db/main.db")
    db_session.global_init("db/main.db")


    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
