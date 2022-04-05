import os
from flask import Flask, render_template, json, request, redirect
import Logger
from Command.parse_command import parse_command
from data import db_session

app = Flask(__name__)
log = Logger.set_logging()

console_outputs = {}

user_chats_opened = {}  # ip: name_of_chat
user_chats_outputs = {'global': []}  # [name1, name2]: outputs


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat/<name>")
def index2(name):
    from Command.commands import get_user_friends

    addr = request.remote_addr

    user_friends = get_user_friends(addr)

    if name not in ['global', *user_friends]:
        return render_template('404.html')

    user_chats_opened[addr] = name

    print(user_friends)

    return render_template("index2.html", user_friends=user_friends)


@app.route('/sendDataChat', methods=["GET", "POST"])
def chat():
    from Command.commands import find_user_by_ip

    addr = request.remote_addr
    name_from = find_user_by_ip(addr)

    # Name To
    name_to = "global"
    try:
        name_to = user_chats_opened[addr]
    except KeyError:
        redirect('global')

    # Making cool name
    if name_from is None:
        name_from = f"Guest {'.'.join(addr.split('.')[:3])}.###"
    name_from = f"[{name_from}]"

    if request.method == "POST":
        textIn = request.form["commandInput"]
        if textIn:
            if name_to == 'global':
                user_chats_outputs['global'].append(f'{name_from} >>>>>> {textIn}')
            else:
                if f'{name_from}-{name_to}' in user_chats_outputs.keys():
                    user_chats_outputs[f'{name_from}-{name_to}'].append(f'{name_from} >>>>>> {textIn}')
                else:
                    user_chats_outputs[f'{name_from}-{name_to}'] = [f'{name_from} >>>>>> {textIn}']

                if f'{name_to}-{name_from}' in user_chats_outputs.keys():
                    user_chats_outputs[f'{name_to}-{name_from}'].append(f'{name_from} >>>>>> {textIn}')
                else:
                    user_chats_outputs[f'{name_to}-{name_from}'] = [f'{name_from} >>>>>> {textIn}']

    if request.method == "GET":
        if name_to == 'global':
            return json.dumps({'outputs': user_chats_outputs['global']})
        else:
            return json.dumps({'outputs': user_chats_outputs[f'{name_from}-{name_to}']})


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

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

