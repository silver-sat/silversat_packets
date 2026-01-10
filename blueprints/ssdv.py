import os
import subprocess
from flask import Blueprint, request, redirect, url_for, render_template
from db import get_db
from utils import get_app_root

bp = Blueprint('ssdv', __name__, url_prefix='/ssdv')

@bp.route('/run', methods=['POST'])
def run():
    payload_file = request.form['payload_file']
    output_image = request.form['output_image']
    processing_run_id = request.form.get('processing_run_id')
    is_ssdv = int(request.form.get('is_ssdv', 0))

    db = get_db()
    payload_file = db.execute("SELECT output_file FROM processing_run WHERE id = ?",(processing_run_id, )).fetchone()[0]

    # payload_file = os.path.join(get_app_root(), payload_file)
    output_image = os.path.join(get_app_root(), output_image)

    if not os.path.exists(payload_file):
        return f"Payload file not found: {payload_file}", 400

    cmd = [
        "/home/tom/ssdv/ssdv", "-d", "-l", "195",
        payload_file,
        output_image
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return f"SSDV processing failed: {e}", 500

    return redirect(url_for('processing.index'))
