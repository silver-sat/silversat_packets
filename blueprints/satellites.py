from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db


bp = Blueprint("satellites", __name__, url_prefix="/satellites")

@bp.route("/")
def list_satellites():
    db = get_db()
    sats = db.execute("SELECT * FROM satellite ORDER BY name").fetchall()
    return render_template("satellites/list.html", sats=sats)

@bp.route("/edit/<int:id>")
def edit_satellite(id):
    db = get_db()
    sat = db.execute("SELECT * FROM satellite WHERE id = ?", (id,)).fetchone()
    return render_template("satellites/edit.html", sat=sat, action_url=url_for("satellites.update_satellite"))

@bp.route("/add")
def add_satellite():
    return render_template("satellites/edit.html", sat=None, action_url=url_for("satellites.create_satellite"))

@bp.route("/create", methods=["POST"])
def create_satellite():
    db = get_db()
    db.execute("""
        INSERT INTO satellite (name, catalog_number, nominal_freq_hz, notes)
        VALUES (?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form["catalog_number"],
        request.form["nominal_freq_hz"],
        request.form.get("notes", "")
    ))
    db.commit()
    return redirect(url_for("satellites.list_satellites"))

@bp.route("/update", methods=["POST"])
def update_satellite():
    db = get_db()
    db.execute("""
        UPDATE satellite SET
            name = ?, catalog_number = ?, nominal_freq_hz = ?, notes = ?
        WHERE id = ?
    """, (
        request.form["name"],
        request.form["catalog_number"],
        request.form["nominal_freq_hz"],
        request.form.get("notes", ""),
        request.form["id"]
    ))
    db.commit()
    return redirect(url_for("satellites.list_satellites"))
