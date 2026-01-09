import os
import subprocess
from flask import Blueprint, request, redirect, url_for, render_template
from db import get_db

bp = Blueprint('ssdv', __name__, url_prefix='/ssdv')

@bp.route('/run', methods=['POST'])
def run():
    payload_file = request.form['payload_file']
    output_image = request.form['output_image']
    processing_run_id = request.form.get('processing_run_id')
    is_ssdv = int(request.form.get('is_ssdv', 0))

    if not os.path.exists(payload_file):
        return f"Payload file not found: {payload_file}", 400

    cmd = [
        "~/ssdv/ssdv", "-d", "-l", "195",
        payload_file,
        output_image
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return f"SSDV processing failed: {e}", 500

    return redirect(url_for('processing.index'))
