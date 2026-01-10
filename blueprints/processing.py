from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
import sys
import subprocess
import requests
from datetime import datetime
import logging
from utils import app_path, resolve_storage_path
import os

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

bp = Blueprint("processing", __name__, url_prefix="/processing")

@bp.route('/') 
def index(): 
    db = get_db() 
    
    last_run = db.execute("SELECT MAX(processing_run_id) FROM packet").fetchone()[0]
    if last_run is not None:        
        packet_count = db.execute("SELECT COUNT(packet_index) FROM packet WHERE processing_run_id=?", (last_run,)).fetchone()[0]
        good_packet_count = db.execute("SELECT COUNT(packet_index) FROM packet WHERE processing_run_id=? AND crc_ok=1", (last_run,)).fetchone()[0]
        cur = db.execute(""" UPDATE processing_run SET packet_count = ?, good_packets = ? WHERE id = ?""", (packet_count, good_packet_count, last_run)) 
        db.commit() 
    
    runs = db.execute("SELECT * FROM processing_run ORDER BY id DESC").fetchall()
    
    return render_template('processing/index.html', runs=runs)

@bp.route('/new', methods=['GET', 'POST']) 
def new(): 
    if request.method == 'POST': 
        # source_file = request.form['source_file']
        capture_session_id = request.form['capture_session_id']
        freq_offset = int(request.form['freq_offset_hz']) 
        doppler_en = int(request.form.get('doppler_en_choice')) 
        access_threshold = int(request.form.get('access_threshold'))
        store_packets = int(request.form.get('store_packets_choice'))
        output_path = 'received_packets/'  # default relative to app root
        ssdv_choice = request.form.get('ssdv')
        notes = request.form['notes']
        
        if ssdv_choice:
                is_ssdv = 1
        else:
                is_ssdv = 0
        
        
        db = get_db() 
        source_file = db.execute("SELECT wav_path FROM capture_session WHERE capture_session.id = ?", (capture_session_id,)).fetchone()[0]
        source_file_resolved = resolve_storage_path(source_file)
        
        # logging.debug("Form data:", dict(request.form))
        # logging.debug(f'capture_session_id: {capture_session_id}')
        start_time_utc = datetime.utcnow().isoformat()
        filename = start_time_utc.replace(":", "").replace("-", "").replace("T", "_") + ".bin"
        
        cur = db.execute(""" INSERT INTO processing_run (source_file, start_time_utc, output_path, capture_session_id, freq_offset_hz, doppler_en, access_threshold, store_packets, is_ssdv, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """, (source_file, start_time_utc, output_path, capture_session_id, freq_offset, doppler_en, access_threshold, store_packets, is_ssdv, notes)) 
        run_id = cur.lastrowid 
        db.commit()
        
        output_file = os.path.join(output_path, filename)
        
        # Launch processing script 
        script_path = app_path("gnuradio", "passdata_playback.py")

        cmd = [ "python3", script_path,
                "--source-file", source_file_resolved,
                "--capture-session-id", capture_session_id,
                "--frequency-offset", str(freq_offset), 
                "--processing-run-id", str(run_id), 
                "--doppler-en", str(doppler_en), 
                "--access-threshold", str(access_threshold),
                "--store-packets", str(store_packets),
                "--output-path", output_path
                ]
        
        # Launch it in the background 
        subprocess.Popen(cmd)
        
        return redirect(url_for('processing.index'))
        
    else:
        db = get_db() 
        sessions = db.execute("SELECT id FROM capture_session ORDER BY id DESC").fetchall() 
        return render_template("processing/new.html", sessions=sessions)
               
    return render_template('processing/new.html')


@bp.route('/<int:id>') 
def view(id): 
    db = get_db() 
    run = db.execute("SELECT * FROM processing_run WHERE id = ?", (id,)).fetchone() 
    packets = db.execute("""
     SELECT * FROM packet WHERE processing_run_id = ? ORDER BY id 
     """, (id,)).fetchall()
    
    return render_template("processing/view.html", run=run, packets=packets)
