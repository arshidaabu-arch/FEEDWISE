from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import sqlite3, uuid, os
from analyzer import analyze_image

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
DB_PATH = BASE_DIR / "smartfeed.db"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("SMARTFEED_SECRET", "change-this-for-local-use")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                feed_type TEXT NOT NULL,
                cattle_type TEXT NOT NULL,
                target_protein REAL,
                measured_protein REAL,
                moisture REAL,
                image_name TEXT,
                visual_result TEXT NOT NULL,
                visual_note TEXT NOT NULL
            )
        """)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def recommendations(result, target, measured, moisture):
    items=[]
    if result == "Possible mould-like pattern":
        items.append("Isolate this sample and arrange a validated laboratory check before feeding.")
    else:
        items.append("No obvious mould-like pattern was flagged by this demo screen; this does not establish safety.")
    if moisture is not None:
        if moisture >= 14:
            items.append("Moisture is elevated for many stored dry feeds. Check the feed-specific limit and improve dry storage.")
        else:
            items.append("Compare moisture with the specification for this particular feed and storage method.")
    if target is not None and measured is not None:
        if measured < target:
            items.append(f"Measured protein is {target-measured:.1f} percentage points below the entered target. Review the ration with a qualified nutritionist.")
        else:
            items.append("Measured protein meets or exceeds the entered target; verify that the value is from a valid test.")
    else:
        items.append("Enter a measured protein value from a suitable test to compare it with the target.")
    items.append("Do not use this prototype's visual result as a mycotoxin test or a definitive feed-safety decision.")
    return items

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        feed_type=request.form.get("feed_type","").strip()
        cattle_type=request.form.get("cattle_type","").strip()
        target=request.form.get("target_protein","").strip()
        measured=request.form.get("measured_protein","").strip()
        moisture=request.form.get("moisture","").strip()
        if not feed_type or not cattle_type:
            flash("Please select the feed type and cattle category.")
            return redirect(url_for("index"))
        try:
            target_v=float(target) if target else None
            measured_v=float(measured) if measured else None
            moisture_v=float(moisture) if moisture else None
            for label, val in [("Target protein",target_v),("Measured protein",measured_v),("Moisture",moisture_v)]:
                if val is not None and (val < 0 or val > 100):
                    raise ValueError(f"{label} must be between 0 and 100.")
        except ValueError as e:
            flash(str(e))
            return redirect(url_for("index"))

        image=request.files.get("image")
        image_name=None
        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Upload a PNG, JPG, JPEG or WEBP image.")
                return redirect(url_for("index"))
            ext=image.filename.rsplit(".",1)[1].lower()
            image_name=f"{uuid.uuid4().hex}.{ext}"
            image.save(UPLOAD_DIR/image_name)
        elif request.form.get("camera_image"):
            import base64
            data=request.form["camera_image"]
            try:
                header, encoded=data.split(",",1)
                if not header.startswith("data:image/"):
                    raise ValueError()
                raw=base64.b64decode(encoded, validate=True)
                if len(raw)>10*1024*1024:
                    raise ValueError()
                image_name=f"{uuid.uuid4().hex}.jpg"
                (UPLOAD_DIR/image_name).write_bytes(raw)
            except Exception:
                flash("Could not read camera image. Please capture it again.")
                return redirect(url_for("index"))

        if image_name:
            visual_result, visual_note=analyze_image(UPLOAD_DIR/image_name)
        else:
            visual_result="Image not provided"
            visual_note="No image was submitted, so visual screening was skipped."

        sample_id="SF-"+datetime.now().strftime("%y%m%d")+"-"+uuid.uuid4().hex[:6].upper()
        created=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db() as conn:
            cur=conn.execute("""INSERT INTO inspections
            (sample_id,created_at,feed_type,cattle_type,target_protein,measured_protein,moisture,image_name,visual_result,visual_note)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (sample_id,created,feed_type,cattle_type,target_v,measured_v,moisture_v,image_name,visual_result,visual_note))
            inspection_id=cur.lastrowid
        return redirect(url_for("result", inspection_id=inspection_id))
    with db() as conn:
        recent=conn.execute("SELECT * FROM inspections ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("index.html", recent=recent)

@app.route("/result/<int:inspection_id>")
def result(inspection_id):
    with db() as conn:
        item=conn.execute("SELECT * FROM inspections WHERE id=?",(inspection_id,)).fetchone()
    if not item:
        flash("Inspection not found.")
        return redirect(url_for("index"))
    recs=recommendations(item["visual_result"],item["target_protein"],item["measured_protein"],item["moisture"])
    return render_template("result.html", item=item, recommendations=recs)

@app.route("/history")
def history():
    with db() as conn:
        rows=conn.execute("SELECT * FROM inspections ORDER BY id DESC").fetchall()
    return render_template("history.html", rows=rows)

@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/delete-history", methods=["POST"])
def delete_history():
    with db() as conn:
        rows=conn.execute("SELECT image_name FROM inspections").fetchall()
        conn.execute("DELETE FROM inspections")
    for row in rows:
        if row["image_name"]:
            try: (UPLOAD_DIR/row["image_name"]).unlink(missing_ok=True)
            except OSError: pass
    flash("Inspection history cleared.")
    return redirect(url_for("history"))

@app.route("/health")
def health():
    return {"status":"ok","app":"SmartFeed AI demo"}

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
