from flask import Blueprint, render_template, request, redirect, send_file, url_for, flash, jsonify, current_app
from werkzeug.exceptions import abort
from db import get_db
from tle_plot import generate_orbit_plots
import requests
from datetime import datetime
import subprocess
import os
from utils import app_path, resolve_storage_path
import logging

bp = Blueprint("captures", __name__, url_prefix="/captures")

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

@bp.route("/")
def index():
    db = get_db()
    
    captures = db.execute("""SELECT capture_session.id, capture_session.start_time_utc, 
        satellite.name AS satellite_name, operator.name AS operator_name, capture_session.wav_path 
        FROM (capture_session 
        INNER JOIN satellite ON capture_session.satellite_id = satellite.id 
        INNER JOIN operator ON capture_session.operator_id = operator.id ) ORDER BY capture_session.id DESC""").fetchall()
        
    return render_template("captures/list.html", captures=captures)
     

@bp.route("/new", methods=["GET", "POST"])
def new():
    db = get_db()
    satellites = db.execute("SELECT id, name FROM satellite ORDER BY name").fetchall()
    locations = db.execute("SELECT * FROM location ORDER BY name").fetchall()

    if request.method == "POST":
        satellite_id = request.form["satellite_id"]
        location_id = request.form["location_id"]
        center_freq = request.form["center_freq_hz"]
        tle1 = request.form["tle_line1"]
        tle2 = request.form["tle_line2"]
        tz = request.form["timezone"]
        if tz == "custom":
            tz = request.form["timezone_custom"]
        notes = request.form["notes"]

        operator_id = 1  # Default Pi user
        created_at = datetime.utcnow().isoformat() 
        
        output_path = request.form["output_path"]
        

        # After inserting the capture session 
        start_time_utc = datetime.utcnow().isoformat() 
        filename = start_time_utc.replace(":", "").replace("-", "").replace("T", "_") + ".wav" 
        wav_path = resolve_storage_path(output_path, filename)
        
        db.execute( 
            """INSERT INTO capture_session 
            (satellite_id, location_id, center_freq_hz, tle_line1, tle_line2, observer_timezone, operator_id, output_path, wav_path, start_time_utc, created_at, notes) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
            (satellite_id, location_id, center_freq, tle1, tle2, tz, operator_id, output_path, wav_path, start_time_utc, created_at, notes))

        db.commit()
        
        os.getcwd
         
        # Build command to run your GNU Radio script
        script_path = app_path("gnuradio", "rtlsdr_iq_capture.py")
        cmd = ["python3",
               script_path,
               "--freq", str(center_freq),
               "--outfile", wav_path
               ]
        # Launch it in the background 
        subprocess.Popen(cmd)
        
        flash("Capture session created.")
        return redirect(url_for("index"))

    return render_template("captures/new.html", satellites=satellites, locations=locations)


@bp.route("/fetch_tle/<int:sat_id>")
def fetch_tle(sat_id):
    db = get_db()
    sat = db.execute("SELECT catalog_number FROM satellite WHERE id = ?", (sat_id,)).fetchone()
    if not sat:
        return jsonify({"error": "Satellite not found"}), 404

    catnum = sat["catalog_number"]
    user = current_app.config["SPACETRACK_USER"]
    pw = current_app.config["SPACETRACK_PASS"]
    
    #logging.debug("catalog number: ", catnum)
    #logging.debug("username: ", user)
    #logging.debug("pwd: ", pw)

    session = requests.Session()
    login_url = "https://www.space-track.org/ajaxauth/login"
    #query_url = f"https://www.space-track.org/basicspacedata/query/class/tle_latest/NORAD_CAT_ID/{catnum}/orderby/ORDINAL asc/format/tle"
    query_url="https://www.space-track.org/basicspacedata/query/class/gp/NORAD_CAT_ID/66909/orderby/TLE_LINE1%20ASC/format/tle"
    
    try:
        session.post(login_url, data={"identity": user, "password": pw})
        resp = session.get(query_url)
        logging.debug("login response: ", resp)
        if resp.ok:
            lines = resp.text.strip().splitlines()
            if len(lines) >= 2:
                return jsonify({
                    "tle_line1": lines[0],
                    "tle_line2": lines[1]
                })
            else:
                return jsonify({"error": "TLE not found"}), 404
        else:
            return jsonify({"error": "Space-Track query failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/preview_orbit", methods=["POST"])
def preview_orbit():
    db = get_db()
    try:
        tle1 = request.form["tle_line1"].strip()
        tle2 = request.form["tle_line2"].strip()

        location_id = request.form["location_id"]
        loc = db.execute("SELECT * FROM location WHERE id = ?", (location_id,)).fetchone()
        lat = loc["lat_deg"]
        lon = loc["lon_deg"]
        elev = loc["elev_m"]

        tz = request.form.get("timezone", "UTC")
        if tz == "custom":
            tz = request.form.get("timezone_custom", "UTC")

        if not tle1 or not tle2:
            return jsonify({"error": "TLE lines cannot be empty"}), 400

        result = generate_orbit_plots(tle1, tle2, lat, lon, elev, tz) 
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
        

@bp.route("/captures/files/<path:filename>") 
def serve_capture_file(filename): 
    # Look up the full path from the database 
    db = get_db() 
    row = db.execute( 
        "SELECT output_path, start_time_utc FROM capture_session WHERE start_time_utc || '.wav' = ?", 
        (filename,) 
        ).fetchone()
        
    if row is None: 
        abort(404)
        
    full_path = resolve_storage_path(row["output_path"], filename)
    if not os.path.exists(full_path): 
        abort(404)
         
    return send_file(full_path, as_attachment=True)
    

@bp.route("/captures/<int:id>/edit", methods=["GET", "POST"])
def edit_capture(id):
    db = get_db()
    if request.method == "POST":
        notes = request.form["notes"]
        db.execute("UPDATE capture_session SET notes = ? WHERE id = ?", (notes, id))
        db.commit()
        return redirect(url_for("captures.index"))

    capture = db.execute("SELECT * FROM capture_session WHERE id = ?", (id,)).fetchone()
    if capture is None:
        abort(404)
    return render_template("captures/edit.html", capture=capture)
    
    
@bp.route("/<int:id>/")
def view_capture(id):
    db = get_db()
    capture_data = db.execute("SELECT * FROM capture_session WHERE id = ?",(id, )).fetchone()
    return render_template("captures/view.html", capture_data=capture_data)
    

@bp.route("/captures/<int:id>/")
def view_capture_2(id):
    db = get_db()
    capture_data = db.execute("SELECT * FROM capture_session WHERE id = ?",(id, )).fetchone()
    return render_template("captures/view.html", capture_data=capture_data)

