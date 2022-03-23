import datetime
from flask import Flask, render_template, json, request
import Logger


app = Flask(__name__)
log = Logger.set_logging()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/post", methods=["GET", "POST"])
def post():
    return "Some Cool text"

@app.route("/update", methods=["GET", "POST"])
def update():
    return ""


if __name__ == "__main__":
    app.run()