from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
import sys
import subprocess
import requests
from datetime import datetime
import logging

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
        output_path = '~/silversat_packets/packets/'  # hard-coded for the moment
        ssdv_choice = request.form.get('ssdv')
        notes = request.form['notes']
        
        if ssdv_choice:
                is_ssdv = 1
        else:
                is_ssdv = 0
        
        
        db = get_db() 
        source_file = db.execute("SELECT wav_path FROM capture_session WHERE capture_session.id = ?", (capture_session_id,)).fetchone()[0]
        
        # logging.debug("Form data:", dict(request.form))
        # logging.debug(f'capture_session_id: {capture_session_id}')
        
        cur = db.execute(""" INSERT INTO processing_run (source_file, start_time_utc, output_path, capture_session_id, freq_offset_hz, doppler_en, access_threshold, store_packets, is_ssdv, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """, (source_file, datetime.utcnow().isoformat(), output_path, capture_session_id, freq_offset, doppler_en, access_threshold, store_packets, is_ssdv, notes)) 
        run_id = cur.lastrowid 
        db.commit()
        
        # Launch processing script 
        cmd = [ "python3", "~/gnuradio/passdata_playback.py",
                "--source-file", source_file,
                "--capture-session-id", capture_session_id,
                "--frequency-offset", str(freq_offset), 
                "--processing-run-id", str(run_id), 
                "--doppler-en", str(doppler_en), 
                "--access-threshold", str(access_threshold),
                "--store-packets", str(store_packets)]
        
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
