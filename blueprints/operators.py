from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db

bp = Blueprint("operators", __name__, url_prefix="/operators")

@bp.route("/")
def list_operators():
    db = get_db()
    ops = db.execute("SELECT * FROM operator ORDER BY name").fetchall()
    return render_template("operators/list.html", ops=ops)

@bp.route("/add")
def add_operator():
    return render_template("operators/add.html")

@bp.route("/create", methods=["POST"])
def create_operator():
    db = get_db()
    db.execute("INSERT INTO operator (name) VALUES (?)", (request.form["name"],))
    db.commit()
    return redirect(url_for("operators.list_operators"))

