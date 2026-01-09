CREATE TABLE IF NOT EXISTS operator (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS satellite (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,
    catalog_number      INTEGER NOT NULL UNIQUE,
    nominal_freq_hz     REAL NOT NULL,
    notes               TEXT
);
CREATE TABLE IF NOT EXISTS tle_history (
    id              INTEGER PRIMARY KEY,
    satellite_id    INTEGER NOT NULL REFERENCES satellite(id),
    epoch_utc       TEXT NOT NULL,
    tle_line1       TEXT NOT NULL,
    tle_line2       TEXT NOT NULL,
    source          TEXT,
    downloaded_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS location (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  lat_deg REAL NOT NULL,
  lon_deg REAL NOT NULL,
  elev_m REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "capture_session" (
	"id"	INTEGER,
	"satellite_id"	INTEGER NOT NULL,
	"operator_id"	INTEGER NOT NULL,
	"start_time_utc"	TEXT NOT NULL,
	"center_freq_hz"	REAL NOT NULL,
	"tle_line1"	TEXT NOT NULL,
	"tle_line2"	TEXT NOT NULL,
	"wav_path"	TEXT NOT NULL,
	"notes"	TEXT,
	"observer_timezone"	TEXT,
	"location_id"	INTEGER,
	"output_path"	TEXT NOT NULL DEFAULT '/home/pi/captures',
	"created_at"	TEXT NOT NULL DEFAULT (datetime('now')),
	PRIMARY KEY("id"),
	FOREIGN KEY("location_id") REFERENCES "location"("id"),
	FOREIGN KEY("operator_id") REFERENCES "operator"("id"),
	FOREIGN KEY("satellite_id") REFERENCES "satellite"("id")
);
CREATE TABLE IF NOT EXISTS "packet" (
	"id"	INTEGER,
	"processing_run_id"	INTEGER NOT NULL,
	"packet_index"	INTEGER NOT NULL,
	"capture_time_utc"	TEXT,
	"length_bytes"	INTEGER NOT NULL,
	"header_hex"	TEXT NOT NULL,
	"header_parity_hex"	TEXT NOT NULL,
	"payload_hex"	TEXT NOT NULL,
	"payload_parity_hex"	TEXT NOT NULL,
	"crc_hex"	TEXT NOT NULL,
	"header_ok"	INTEGER NOT NULL,
	"payload_ok"	INTEGER NOT NULL,
	"crc_ok"	INTEGER NOT NULL,
	"scrambler_ok"	INTEGER NOT NULL,
	"packet_error_type"	TEXT,
	"payload_byte_count"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("processing_run_id") REFERENCES "processing_run"("id")
);

CREATE TABLE IF NOT EXISTS "processing_run" (
	"id"	INTEGER,
	"capture_session_id"	NUMERIC NOT NULL,
	"start_time_utc"	TEXT NOT NULL,
	"freq_offset_hz"	REAL,
	"output_path"	TEXT NOT NULL,
	"notes"	TEXT,
	"doppler_en"	INTEGER NOT NULL,
	"store_packets"	INTEGER NOT NULL,
	"source_file"	TEXT NOT NULL,
	"access_threshold"	INTEGER,
	"packet_count"	INTEGER,
	"good_packets"	INTEGER, is_ssdv INTEGER DEFAULT 0,
	PRIMARY KEY("id"),
	FOREIGN KEY("capture_session_id") REFERENCES "capture_session"("id")
);
CREATE TABLE IF NOT EXISTS ssdv_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload_file TEXT NOT NULL,
    output_image TEXT NOT NULL,
    run_time_utc TEXT DEFAULT CURRENT_TIMESTAMP,
    processing_run_id INTEGER REFERENCES processing_run(id)
);
