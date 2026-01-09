from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db

bp = Blueprint("locations", __name__, url_prefix="/locations")

@bp.route("/")
def index():
    db = get_db()
    locations = db.execute("SELECT * FROM location ORDER BY name").fetchall()
    return render_template("locations/index.html", locations=locations)

@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        name = request.form["name"]
        lat = request.form["lat_deg"]
        lon = request.form["lon_deg"]
        elev = request.form["elev_m"]

        db = get_db()
        db.execute(
            "INSERT INTO location (name, lat_deg, lon_deg, elev_m) VALUES (?, ?, ?, ?)",
            (name, lat, lon, elev)
        )
        db.commit()
        flash("Location added.")
        return redirect(url_for("locations.index"))

    return render_template("locations/new.html")

@bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()
    location = db.execute("SELECT * FROM location WHERE id = ?", (id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        lat = request.form["lat_deg"]
        lon = request.form["lon_deg"]
        elev = request.form["elev_m"]

        db.execute(
            "UPDATE location SET name = ?, lat_deg = ?, lon_deg = ?, elev_m = ? WHERE id = ?",
            (name, lat, lon, elev, id)
        )
        db.commit()
        flash("Location updated.")
        return redirect(url_for("locations.index"))

    return render_template("locations/edit.html", location=location)
