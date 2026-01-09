from flask import Blueprint, render_template
from db import get_db

bp = Blueprint("packet", __name__, url_prefix="/packet")

@bp.route("/<int:id>")
def detail(id):
    db = get_db()
    packet = db.execute("SELECT * FROM packet WHERE id = ?", (id,)).fetchone()
    return render_template("packet/detail.html", packet=packet)
