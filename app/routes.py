from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/index.html")
@main.route("/")
def index():
    return render_template("index.html")


@main.route("/upload.html")
def upload():
    return render_template("upload.html")


@main.route("/settings.html")
def settings():
    return render_template("settings.html")


@main.route("/results.html")
def results():
    return render_template("results.html")
