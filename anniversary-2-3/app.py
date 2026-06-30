import os, uuid, sqlite3
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

BASE_DIR   = os.path.dirname(__file__)
DB_PATH    = os.path.join(BASE_DIR, 'anniversary.db')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
MAX_DIM    = 1200   # resize large images to save space

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── DB SETUP ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS hugs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT,
            memory   TEXT NOT NULL,
            img_path TEXT,
            created  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS memories (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT,
            tag      TEXT,
            text     TEXT NOT NULL,
            img_path TEXT,
            lat      REAL,
            lng      REAL,
            location_name TEXT,
            created  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS milestones (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            date    TEXT,
            label   TEXT NOT NULL,
            note    TEXT,
            emoji   TEXT DEFAULT '♡',
            type    TEXT DEFAULT 'normal',
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS places (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            label    TEXT NOT NULL,
            note     TEXT,
            emoji    TEXT DEFAULT '📍',
            lat      REAL NOT NULL,
            lng      REAL NOT NULL,
            date     TEXT,
            img_path TEXT,
            created  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

init_db()

# migrate existing DBs that lack the new columns
def migrate_db():
    with get_db() as db:
        cols = [r[1] for r in db.execute("PRAGMA table_info(memories)").fetchall()]
        if 'lat' not in cols:
            db.execute("ALTER TABLE memories ADD COLUMN lat REAL")
        if 'lng' not in cols:
            db.execute("ALTER TABLE memories ADD COLUMN lng REAL")
        if 'location_name' not in cols:
            db.execute("ALTER TABLE memories ADD COLUMN location_name TEXT")
        pcols = [r[1] for r in db.execute("PRAGMA table_info(places)").fetchall()]
        if 'img_path' not in pcols:
            db.execute("ALTER TABLE places ADD COLUMN img_path TEXT")

migrate_db()

# ── IMAGE HELPER ──────────────────────────────────────────
ALLOWED = {'png','jpg','jpeg','gif','webp'}

def allowed(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED

def save_image(file_obj):
    if not file_obj or not allowed(file_obj.filename):
        return None
    ext  = file_obj.filename.rsplit('.',1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, name)
    img  = Image.open(file_obj.stream)
    img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    img.save(path, optimize=True, quality=85)
    return name   # store only filename; serve via /static/uploads/<name>

# ── SERVE FRONTEND ────────────────────────────────────────
@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'templates', 'index.html'))

@app.route('/static/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ══════════════════════════════════════════════════════════
# HUGS
# ══════════════════════════════════════════════════════════
@app.route('/api/hugs', methods=['GET'])
def get_hugs():
    with get_db() as db:
        rows = db.execute("SELECT * FROM hugs ORDER BY created DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/hugs', methods=['POST'])
def add_hug():
    date   = request.form.get('date','')
    memory = request.form.get('memory','').strip()
    if not memory:
        return jsonify({'error':'memory is required'}), 400
    img_path = save_image(request.files.get('image'))
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO hugs (date,memory,img_path) VALUES (?,?,?)",
            (date, memory, img_path)
        )
        row = db.execute("SELECT * FROM hugs WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/hugs/<int:hug_id>', methods=['DELETE'])
def delete_hug(hug_id):
    with get_db() as db:
        row = db.execute("SELECT img_path FROM hugs WHERE id=?", (hug_id,)).fetchone()
        if row and row['img_path']:
            try: os.remove(os.path.join(UPLOAD_DIR, row['img_path']))
            except: pass
        db.execute("DELETE FROM hugs WHERE id=?", (hug_id,))
    return jsonify({'deleted': hug_id})

# ══════════════════════════════════════════════════════════
# MEMORIES
# ══════════════════════════════════════════════════════════
@app.route('/api/memories', methods=['GET'])
def get_memories():
    with get_db() as db:
        rows = db.execute("SELECT * FROM memories ORDER BY created DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/memories', methods=['POST'])
def add_memory():
    date = request.form.get('date','')
    tag  = request.form.get('tag','').strip()
    text = request.form.get('text','').strip()
    if not text:
        return jsonify({'error':'text is required'}), 400
    lat  = request.form.get('lat', None)
    lng  = request.form.get('lng', None)
    location_name = request.form.get('location_name','').strip()
    img_path = save_image(request.files.get('image'))
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO memories (date,tag,text,img_path,lat,lng,location_name) VALUES (?,?,?,?,?,?,?)",
            (date, tag, text, img_path,
             float(lat) if lat else None,
             float(lng) if lng else None,
             location_name or None)
        )
        row = db.execute("SELECT * FROM memories WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/memories/<int:mem_id>', methods=['DELETE'])
def delete_memory(mem_id):
    with get_db() as db:
        row = db.execute("SELECT img_path FROM memories WHERE id=?", (mem_id,)).fetchone()
        if row and row['img_path']:
            try: os.remove(os.path.join(UPLOAD_DIR, row['img_path']))
            except: pass
        db.execute("DELETE FROM memories WHERE id=?", (mem_id,))
    return jsonify({'deleted': mem_id})

# ══════════════════════════════════════════════════════════
# MILESTONES
# ══════════════════════════════════════════════════════════
@app.route('/api/milestones', methods=['GET'])
def get_milestones():
    with get_db() as db:
        rows = db.execute("SELECT * FROM milestones ORDER BY date ASC, created ASC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/milestones', methods=['POST'])
def add_milestone():
    data  = request.get_json()
    label = (data.get('label') or '').strip()
    if not label:
        return jsonify({'error':'label is required'}), 400
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO milestones (date,label,note,emoji,type) VALUES (?,?,?,?,?)",
            (data.get('date',''), label,
             data.get('note',''), data.get('emoji','♡'), data.get('type','normal'))
        )
        row = db.execute("SELECT * FROM milestones WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/milestones/<int:ms_id>', methods=['DELETE'])
def delete_milestone(ms_id):
    with get_db() as db:
        db.execute("DELETE FROM milestones WHERE id=?", (ms_id,))
    return jsonify({'deleted': ms_id})

# ══════════════════════════════════════════════════════════
# PLACES
# ══════════════════════════════════════════════════════════
@app.route('/api/places', methods=['GET'])
def get_places():
    with get_db() as db:
        rows = db.execute("SELECT * FROM places ORDER BY created ASC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/places', methods=['POST'])
def add_place():
    # Accept both JSON and multipart form (for image upload)
    if request.content_type and 'multipart' in request.content_type:
        label = (request.form.get('label') or '').strip()
        lat   = request.form.get('lat')
        lng   = request.form.get('lng')
        note  = request.form.get('note', '')
        emoji = request.form.get('emoji', '📍')
        date  = request.form.get('date', '')
        img_path = save_image(request.files.get('image'))
    else:
        data  = request.get_json()
        label = (data.get('label') or '').strip()
        lat   = data.get('lat')
        lng   = data.get('lng')
        note  = data.get('note', '')
        emoji = data.get('emoji', '📍')
        date  = data.get('date', '')
        img_path = None
    if not label or lat is None or lng is None:
        return jsonify({'error': 'label, lat, lng are required'}), 400
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO places (label,note,emoji,lat,lng,date,img_path) VALUES (?,?,?,?,?,?,?)",
            (label, note, emoji or '📍', float(lat), float(lng), date, img_path)
        )
        row = db.execute("SELECT * FROM places WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route('/api/places/<int:place_id>', methods=['DELETE'])
def delete_place(place_id):
    with get_db() as db:
        row = db.execute("SELECT img_path FROM places WHERE id=?", (place_id,)).fetchone()
        if row and row['img_path']:
            try: os.remove(os.path.join(UPLOAD_DIR, row['img_path']))
            except: pass
        db.execute("DELETE FROM places WHERE id=?", (place_id,))
    return jsonify({'deleted': place_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=False)