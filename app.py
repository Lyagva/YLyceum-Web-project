import os

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
    textIn = request.form["commandInput"]
    textOut = parse_command(request.remote_addr, textIn)

    outputText = f">>> {textIn}\n\n{textOut}"

    return json.dumps({"outputText": outputText})


if __name__ == "__main__":
    # LOCALHOST
    # app.run()

    # HEROKU
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    pass