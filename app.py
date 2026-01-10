from flask import Flask, render_template, g, session
from db import get_db, init_db
import os
from utils import resolve_storage_path

# Import blueprints
from blueprints.captures import bp as captures_bp
from blueprints.satellites import bp as satellites_bp
from blueprints.operators import bp as operators_bp
from blueprints.processing import bp as processing_bp
from blueprints.packet import bp as packet_bp
from blueprints.locations import bp as locations_bp
from blueprints.ssdv import bp as ssdv_bp


def create_app():
    app = Flask(__name__)
    app.config['DATABASE'] = os.path.join(app.root_path, 'observations.db')
    app.secret_key = 'replace-this-with-a-secure-key'
    
    app.config.from_prefixed_env()
    app.config["SPACETRACK_USER"] = os.getenv('SPACETRACK_USER')
    app.config["SPACETRACK_PASS"] = os.getenv('SPACETRACK_PASS')

    # Initialize the database
    with app.app_context():
        init_db()

    # Register blueprints
    app.register_blueprint(captures_bp)
    app.register_blueprint(satellites_bp)
    app.register_blueprint(operators_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(packet_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(ssdv_bp)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
        else:
            g.user = get_db().execute(
                "SELECT * FROM user WHERE id = ?", (user_id,)
            ).fetchone()


    # Home route: show recent capture sessions
    @app.route("/")
    def index():
        db = get_db()
        captures = db.execute("SELECT * FROM capture_session ORDER BY start_time_utc DESC").fetchall() 
     
        # Build list with file size info 
        capture_list = [] 
        for row in captures: 
            filename = row["start_time_utc"].replace(":", "").replace("-", "").replace("T", "_") + ".wav" 
            full_path = resolve_storage_path(row["output_path"], filename)
             
            try: 
                size_bytes = os.path.getsize(full_path) 
                for unit in ['B', 'KB', 'MB', 'GB']: 
                    if size_bytes < 1024: 
                        size_str = f"{size_bytes:.1f} {unit}" 
                        break 
                    size_bytes /= 1024 
                else: 
                    size_str = f"{size_bytes:.1f} TB" 
            except FileNotFoundError: 
                size_str = "N/A" 
                
            capture_list.append(
                { **dict(row), "filename": filename, "filesize": size_str }
            )
             
        return render_template("index.html", captures=capture_list)
        

    @app.template_filter('filesize')
    def filesize(path):
        try:
            size = os.path.getsize(path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except Exception:
            return "N/A"

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
