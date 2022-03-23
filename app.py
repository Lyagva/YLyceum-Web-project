import datetime
from flask import Flask, render_template, json, request
import Logger


app = Flask(__name__)
log = Logger.set_logging()


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()