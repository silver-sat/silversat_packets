"""
Doppler IQ Playback Block (Complex Output)
------------------------------------------

This GNU Radio Embedded Python block plays back a stereo WAV file containing IQ samples
and computes the Doppler-shifted satellite frequency difference relative to the SDR
center frequency. It publishes the difference in sync with the playback once per second
via a message port.

Requirements:
    - Input WAV file must be stereo (2 channels).
    - Left channel = I (in-phase) samples.
    - Right channel = Q (quadrature) samples.
    - WAV filename must contain a timestamp in the format: "_HH-MM-SS_DD-MM-YYYY"
      for proper playback alignment.

Inputs:
    None (reads directly from WAV file)

Outputs:
    One complex64 stream (I + jQ)

Message Ports:
    "freq" → publishes center frequency difference (Hz)

Author: Douglas C. Papay <k8dp.doug@gmail.com>
License: GPLv3

Modified by Tom Conrad for use with Silversat_packets system
Adds the ability to read in parameters from an SQLite database
Needs Parameter block in .grc script to pass the capture_session_id,
which is a table in the database that holds the setup parameters
"""

import numpy as np
import ephem
import datetime
import wave
import re
import pmt
from gnuradio import gr
import zoneinfo   # Python 3.9+
import sqlite3
import sys
import os

# Ensure project root is on sys.path so we can import `db.py` located notionally at
# /home/pi/silversat_packets. Adjust this path if your project is elsewhere.
_PROJECT_ROOT = os.path.join(os.getcwd(), "silversat_packets")
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    import db
    get_db = db.get_db
    DB_PATH = os.path.join(_PROJECT_ROOT, "observations.db")
except Exception:
    db = None
    get_db = None



C = 299792458.0  # speed of light in m/s

class blk(gr.sync_block):
    """
    Doppler IQ Playback Block (Complex Output)

    This block plays back a stereo WAV file containing IQ samples and computes
    the Doppler-shifted satellite frequency relative to the SDR center frequency.
    It publishes the difference in sync with the playback once per second via a 
    message port.

    Output:
        One complex64 stream (I + jQ)
        
    Message Ports:
        "freq" → publishes center frequency difference (Hz)
    """

    def __init__(self,
                 wav_file="",
                 tle_file="",
                 catalog_number=0,
                 sat_freq_hz=0.0,
                 center_freq_hz=0.0,
                 lat="", lon="", elev=0,
                 capture_session_id=0,
                 timezone="America/NewYork",
                 debug=True
                 ):
        """
        Initialize the Doppler IQ Playback block.

        Opens the stereo WAV file if provided, sets up the observer location,
        loads the satellite TLE by catalog number, and parses the start time
        from the filename (local → UTC).

        Args:
            wav_file (str): Path to stereo WAV file containing IQ samples.
            tle_file (str): Path to TLE file containing satellite orbital elements.
            catalog_number (int): Satellite catalog number (e.g., 66909).
            sat_freq_hz (float): Satellite nominal frequency in Hz.
            center_freq_hz (float): SDR spectrum center frequency in Hz.
            lat (str): Observer latitude.
            lon (str): Observer longitude.
            elev (float): Observer elevation in meters.
            timezone (str): Local timezone for filename timestamps.
            debug (bool): Enable debug prints.
        """
        gr.sync_block.__init__(
            self,
            name='Doppler IQ Playback',
            in_sig=None,
            out_sig=[np.complex64]  # single complex output stream
        )
        

        # Register message output port
        self.message_port_register_out(pmt.intern("freq"))
        
        self.capture_session_id = capture_session_id
        self.start_time_utc = 0
        
        if capture_session_id:
            try: 
                db = get_db()
                conn = sqlite3.connect(DB_PATH) 
                cur = conn.cursor()
                
                capture_setup = db.execute("SELECT * FROM capture_session WHERE id = ?", (capture_session_id,)).fetchone()
                location_info = db.execute("SELECT * FROM location WHERE id = ?", (capture_setup["location_id"],)).fetchone()
                satellite_info = db.execute("SELECT * FROM satellite WHERE id = ?", (capture_setup["satellite_id"],)).fetchone()
                self.wav_file = capture_setup["lat_deg"]
                
                # i'm not storing tle's in a file, so I can jump ahead to assigning them to variables
                line1 = capture_setup["tle_line_1"]
                line2 = capture_setup["tle_line_2"]
                self.catalog_number = satellite_info["catalog_number"]
                self.sat_freq_hz = satellite_info["nominal_freq_hz"]
                self.center_freq_hz = capture_setup["center_freq_hz"]
                self.lat = location_info["lat_deg"]
                self.lon = location_info["lon_deg"]
                self.elev = location_info["elev_m"]
                self.timezone = capture_setup["observer_timezone"]
                self.start_time_utc = capture_setup["start_time_utc"]
                self.debug = debug
                conn.close()
                
                parts = line1.split()
                if len(parts) > 1:
                    catnum = parts[1]  # e.g. "66909U"
                    catnum_digits = ''.join(ch for ch in catnum if ch.isdigit())

                    if catnum_digits == self.catalog_number:
                        self.sat = ephem.readtle(name, line1, line2)
                        if self.debug:
                            print(f"[DEBUG] Loaded satellite {name} with catalog {catnum_digits}")
                            print("[DEBUG] Line1:", line1)
                            print("[DEBUG] Line2:", line2)

                if self.sat is None and self.debug:
                    print(f"[DEBUG] Catalog number {self.catalog_number} not found in file")
                
            except Exception as e: 
                print(f"[doppler] DB error: {e}")
        else:
            # Parameters
            self.wav_file = wav_file
            self.tle_file = tle_file
            self.catalog_number = str(catalog_number)
            self.sat_freq_hz = float(sat_freq_hz)
            self.center_freq_hz = float(center_freq_hz)
            self.lat = str(lat)
            self.lon = str(lon)
            self.elev = float(elev)
            self.timezone = timezone
            self.debug = debug

        # Open WAV (only if provided)
        self.wav = None
        self.channels = 1
        self.sample_rate = 1
        if self.wav_file:
            self.wav = wave.open(self.wav_file, 'rb')
            self.channels = self.wav.getnchannels()
            self.sample_rate = self.wav.getframerate()
            print(f'wav file framerate: {self.wav.getframerate()}')

            # Require stereo WAV file
            if self.channels != 2:
                raise ValueError(
                    f"WAV file {self.wav_file} must be stereo (2 channels), "
                    f"but has {self.channels} channel(s)."
                )

            if self.debug:
                print(f"[DEBUG] Opened WAV file: {self.wav_file}, "
                      f"Channels: {self.channels}, SampleRate: {self.sample_rate}")

        # Observer setup
        self.observer = ephem.Observer()
        self.observer.lat = self.lat if self.lat else "0"
        self.observer.lon = self.lon if self.lon else "0"
        self.observer.elevation = self.elev

        # Load TLE by catalog number
        if capture_session_id == 0:
            self.sat = None
            if self.tle_file:
                with open(self.tle_file, 'r') as f:
                    lines = [ln.strip() for ln in f if ln.strip()]
                total_sats = len(lines) // 3
                if self.debug:
                    print(f"[DEBUG] TLE file has {total_sats} satellites")

                for i in range(total_sats):
                    name  = lines[i*3]
                    line1 = lines[i*3 + 1]
                    line2 = lines[i*3 + 2]

                    parts = line1.split()
                    if len(parts) > 1:
                        catnum = parts[1]  # e.g. "66909U"
                        catnum_digits = ''.join(ch for ch in catnum if ch.isdigit())

                        if catnum_digits == self.catalog_number:
                            self.sat = ephem.readtle(name, line1, line2)
                            if self.debug:
                                print(f"[DEBUG] Loaded satellite {name} with catalog {catnum_digits}")
                                print("[DEBUG] Line1:", line1)
                                print("[DEBUG] Line2:", line2)
                            break

                if self.sat is None and self.debug:
                    print(f"[DEBUG] Catalog number {self.catalog_number} not found in file")

        if self.start_time_utc:
            self.start_time = self.start_time_utc
        else:
            # Parse date/time from filename (local → UTC)
            self.start_play = datetime.datetime.utcnow()  # fallback
            match = re.search(r'_(\d{2}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{4})', self.wav_file)
            if match:
                timestr, datestr = match.groups()
                try:
                    local_dt = datetime.datetime.strptime(
                        timestr + "_" + datestr, "%H-%M-%S_%d-%m-%Y"
                    )
                    local_dt = local_dt.replace(tzinfo=zoneinfo.ZoneInfo(self.timezone))
                    self.start_play = local_dt.astimezone(zoneinfo.ZoneInfo("UTC"))
                    if self.debug:
                        print("[DEBUG] Parsed local time:", local_dt)
                        print("[DEBUG] Converted to UTC:", self.start_play)
                except ValueError:
                    if self.debug:
                        print("[DEBUG] Failed to parse start time, using UTC fallback")

        # Local variables
        self.sample_counter = 0
        self.next_update = 0

    def work(self, input_items, output_items):
        """
        Process audio samples and compute frequency difference.

        Reads frames from the stereo WAV file, outputs complex IQ stream,
        and once per second computes the Doppler-shifted satellite frequency
        relative to the SDR center frequency. Publishes the difference via
        the "freq" message port.

        Args:
            input_items (list): Input streams (unused).
            output_items (list): Output stream (complex IQ samples).

        Returns:
            int: Number of output items produced, or -1 if end of file.
        """
        out = output_items[0]
        n = len(out)

        # Audio playback
        if self.wav is not None:
            frames = self.wav.readframes(n)
            
            if not frames:
                out[:] = 0.0 + 0.0j
                return -1
            data = np.frombuffer(frames, dtype=np.float32) #.astype(np.float32)

            # Stereo IQ required
            stereo = data.reshape(-1, 2)
            # i_data = stereo[:, 0] / 2147483648.0
            # q_data = stereo[:, 1] / 2147483648.0
            i_data = stereo[:, 0]
            q_data = stereo[:, 1]
            
            iq = i_data[:n] + 1j * q_data[:n]
            if len(iq) < n:
                iq = np.pad(iq, (0, n - len(iq)), constant_values=0)
            out[:] = iq
        else:
            out[:] = 0.0 + 0.0j
        
        
        # Advance sample counter
        self.sample_counter += n

        # Center difference calculation once per second
        if self.sat is not None and self.sat_freq_hz > 0.0 and self.center_freq_hz > 0.0:
            if self.sample_counter >= self.next_update:
                current_dt = self.start_play + datetime.timedelta(
                    seconds=self.sample_counter / self.sample_rate
                )
                self.observer.date = current_dt
                self.sat.compute(self.observer)
                rel_vel = self.sat.range_velocity

                # Doppler-shifted satellite frequency
                sat_doppler_freq = self.sat_freq_hz * (1 - rel_vel / C)

                # Difference to SDR center
                center_diff = sat_doppler_freq - self.center_freq_hz

                if self.debug:
                    print(f"[DEBUG] Time: {current_dt}, RelVel: {rel_vel:.2f} m/s, "
                          f"SatFreq+Doppler: {sat_doppler_freq:.2f} Hz, "
                          f"CenterDiff: {center_diff:.2f} Hz")

                # Publish only the center difference value via "freq" port
                self.message_port_pub(
                    pmt.intern("freq"),
                    pmt.cons(pmt.intern("center_diff"),
                             pmt.from_double(center_diff))
                )

                # Schedule next update one second later
                self.next_update += self.sample_rate

        return n

