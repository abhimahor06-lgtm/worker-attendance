"""
============================================================
  CONTRACTOR REGISTER APP — Flask Backend
  Author  : Thekedaar Panel
  Database: SQLite (auto-created on first run)
  Run     : python app.py
  Open    : http://127.0.0.1:5000
============================================================
"""

from flask import Flask, jsonify, request, render_template, g
import sqlite3, os, calendar
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thekedaar-2025-secret'

# ─── DATABASE PATH ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'database', 'app.db')

# ─── DB CONNECTION HELPERS ───────────────────────────────────
def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA journal_mode = WAL")
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_db', None)
    if db: db.close()

def qry(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows

def run(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

# ─── CREATE ALL TABLES ───────────────────────────────────────
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = WAL;

        CREATE TABLE IF NOT EXISTS workers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            mobile_number TEXT    NOT NULL UNIQUE,
            role          TEXT    NOT NULL CHECK(role IN ('mistri','labour')),
            daily_rate    REAL    NOT NULL DEFAULT 0,
            aadhar_number TEXT,
            address       TEXT,
            joining_date  TEXT    DEFAULT (date('now','localtime')),
            is_active     INTEGER DEFAULT 1,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id   INTEGER NOT NULL,
            att_date    TEXT    NOT NULL,
            month_year  TEXT    NOT NULL,
            day_number  INTEGER NOT NULL CHECK(day_number BETWEEN 1 AND 31),
            status      TEXT    NOT NULL CHECK(status IN ('P','A','H','HD')),
            day_value   REAL    NOT NULL DEFAULT 1.0,
            created_at  TEXT    DEFAULT (datetime('now','localtime')),
            updated_at  TEXT    DEFAULT (datetime('now','localtime')),
            UNIQUE(worker_id, att_date),
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS extra_money (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id   INTEGER NOT NULL,
            month_label TEXT    NOT NULL,
            month_year  TEXT,
            amount      REAL    NOT NULL,
            reason      TEXT,
            entry_date  TEXT    DEFAULT (date('now','localtime')),
            created_at  TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS payments (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id    INTEGER NOT NULL,
            month_year   TEXT    NOT NULL,
            amount       REAL    NOT NULL,
            payment_type TEXT    DEFAULT 'salary' CHECK(payment_type IN ('salary','advance','bonus','deduction')),
            payment_mode TEXT    DEFAULT 'cash'   CHECK(payment_mode IN ('cash','upi','bank','cheque')),
            payment_date TEXT    DEFAULT (date('now','localtime')),
            notes        TEXT,
            created_at   TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_att_worker_month ON attendance(worker_id, month_year);
        CREATE INDEX IF NOT EXISTS idx_att_date         ON attendance(att_date);
        CREATE INDEX IF NOT EXISTS idx_extra_worker     ON extra_money(worker_id);
        CREATE INDEX IF NOT EXISTS idx_pay_worker_month ON payments(worker_id, month_year);
    """)
    db.commit()
    db.close()
    print("✅  Database tables ready:", DB_PATH)

# ─────────────────────────────────────────────────────────────
#  PAGE ROUTE
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('register.html')

# ─────────────────────────────────────────────────────────────
#  WORKERS API
# ─────────────────────────────────────────────────────────────
@app.route('/api/workers', methods=['GET'])
def api_get_workers():
    rows = qry("""
        SELECT * FROM workers
        WHERE is_active = 1
        ORDER BY role, full_name
    """)
    return jsonify([dict(r) for r in rows])

@app.route('/api/workers', methods=['POST'])
def api_add_worker():
    d      = request.get_json() or {}
    name   = (d.get('full_name') or '').strip()
    mobile = (d.get('mobile_number') or '').strip()
    role   = d.get('role', 'labour')
    rate   = float(d.get('daily_rate') or 0)
    aadhar = (d.get('aadhar_number') or '').strip()
    addr   = (d.get('address') or '').strip()
    jdate  = (d.get('joining_date') or date.today().isoformat()).strip()

    if not name:   return jsonify({'error': 'Full name zaroori hai'}), 400
    if not mobile: return jsonify({'error': 'Mobile number zaroori hai'}), 400
    if rate < 1:   return jsonify({'error': 'Daily rate valid hona chahiye (min ₹1)'}), 400
    if role not in ('mistri', 'labour'):
        return jsonify({'error': 'Role sirf mistri ya labour ho sakta hai'}), 400

    dup = qry("SELECT id FROM workers WHERE mobile_number=?", [mobile], one=True)
    if dup:
        return jsonify({'error': 'Yeh mobile number pehle se registered hai'}), 400

    wid = run("""
        INSERT INTO workers (full_name, mobile_number, role, daily_rate, aadhar_number, address, joining_date)
        VALUES (?,?,?,?,?,?,?)
    """, [name, mobile, role, rate, aadhar, addr, jdate])

    w = qry("SELECT * FROM workers WHERE id=?", [wid], one=True)
    return jsonify({'success': True, 'worker': dict(w)}), 201

@app.route('/api/workers/<int:wid>', methods=['PUT'])
def api_update_worker(wid):
    d = request.get_json() or {}
    w = qry("SELECT id FROM workers WHERE id=?", [wid], one=True)
    if not w: return jsonify({'error': 'Worker nahi mila'}), 404

    name   = (d.get('full_name') or '').strip()
    mobile = (d.get('mobile_number') or '').strip()
    role   = d.get('role', 'labour')
    rate   = float(d.get('daily_rate') or 0)

    if not name:   return jsonify({'error': 'Full name zaroori hai'}), 400
    if not mobile: return jsonify({'error': 'Mobile number zaroori hai'}), 400
    if rate < 1:   return jsonify({'error': 'Daily rate valid hona chahiye'}), 400

    dup = qry("SELECT id FROM workers WHERE mobile_number=? AND id!=?", [mobile, wid], one=True)
    if dup: return jsonify({'error': 'Yeh mobile number kisi aur ka hai'}), 400

    run("""
        UPDATE workers SET full_name=?, mobile_number=?, role=?, daily_rate=?,
            aadhar_number=?, address=?, joining_date=?
        WHERE id=?
    """, [name, mobile, role, rate,
          (d.get('aadhar_number') or '').strip(),
          (d.get('address') or '').strip(),
          (d.get('joining_date') or date.today().isoformat()),
          wid])

    updated = qry("SELECT * FROM workers WHERE id=?", [wid], one=True)
    return jsonify({'success': True, 'worker': dict(updated)})

@app.route('/api/workers/<int:wid>', methods=['DELETE'])
def api_delete_worker(wid):
    w = qry("SELECT full_name FROM workers WHERE id=?", [wid], one=True)
    if not w: return jsonify({'error': 'Worker nahi mila'}), 404
    run("DELETE FROM workers WHERE id=?", [wid])
    return jsonify({'success': True, 'message': f'{w["full_name"]} delete ho gaya'})

# ─────────────────────────────────────────────────────────────
#  ATTENDANCE API
# ─────────────────────────────────────────────────────────────
STATUS_VALUE = {'P': 1.0, 'A': 0.0, 'H': 0.5, 'HD': 1.0}

@app.route('/api/attendance/<month_year>', methods=['GET'])
def api_get_attendance(month_year):
    rows = qry("""
        SELECT worker_id, day_number, status
        FROM   attendance
        WHERE  month_year = ?
    """, [month_year])
    # { worker_id: { "1": "P", "2": "A", ... } }
    result = {}
    for r in rows:
        wid = str(r['worker_id'])
        result.setdefault(wid, {})[str(r['day_number'])] = r['status']
    return jsonify(result)

@app.route('/api/attendance', methods=['POST'])
def api_mark_attendance():
    d          = request.get_json() or {}
    worker_id  = d.get('worker_id')
    day        = int(d.get('day', 0))
    month_year = (d.get('month_year') or '').strip()   # "2025-12"
    status     = (d.get('status') or '').strip()       # P / A / H / HD / "" to clear

    if not worker_id or not day or not month_year:
        return jsonify({'error': 'worker_id, day aur month_year zaroori hain'}), 400

    try:
        y, m = map(int, month_year.split('-'))
        att_date = f"{y:04d}-{m:02d}-{day:02d}"
    except Exception:
        return jsonify({'error': 'month_year format galat hai (YYYY-MM chahiye)'}), 400

    if not status:
        # Clear the record
        run("DELETE FROM attendance WHERE worker_id=? AND att_date=?", [worker_id, att_date])
        return jsonify({'success': True, 'action': 'cleared', 'status': ''})

    if status not in STATUS_VALUE:
        return jsonify({'error': f'Status "{status}" invalid hai. P/A/H/HD hona chahiye'}), 400

    day_value = STATUS_VALUE[status]
    existing  = qry("SELECT id FROM attendance WHERE worker_id=? AND att_date=?",
                    [worker_id, att_date], one=True)
    if existing:
        run("""
            UPDATE attendance
            SET status=?, day_value=?, updated_at=datetime('now','localtime')
            WHERE worker_id=? AND att_date=?
        """, [status, day_value, worker_id, att_date])
    else:
        run("""
            INSERT INTO attendance (worker_id, att_date, month_year, day_number, status, day_value)
            VALUES (?,?,?,?,?,?)
        """, [worker_id, att_date, month_year, day, status, day_value])

    return jsonify({'success': True, 'status': status, 'day_value': day_value})

# ─────────────────────────────────────────────────────────────
#  EXTRA MONEY API
# ─────────────────────────────────────────────────────────────
@app.route('/api/extra_money', methods=['GET'])
def api_get_all_extra():
    wid = request.args.get('worker_id')
    if wid:
        rows = qry("""
            SELECT * FROM extra_money WHERE worker_id=?
            ORDER BY month_year DESC, created_at DESC
        """, [wid])
    else:
        rows = qry("SELECT * FROM extra_money ORDER BY created_at DESC")
    return jsonify([dict(r) for r in rows])

@app.route('/api/extra_money', methods=['POST'])
def api_add_extra():
    d         = request.get_json() or {}
    worker_id = d.get('worker_id')
    label     = (d.get('month_label') or '').strip()
    amount    = float(d.get('amount') or 0)
    reason    = (d.get('reason') or '').strip()
    my        = (d.get('month_year') or '').strip()

    if not worker_id: return jsonify({'error': 'worker_id zaroori hai'}), 400
    if not label:     return jsonify({'error': 'Month label zaroori hai'}), 400
    if amount <= 0:   return jsonify({'error': 'Amount 0 se zyada hona chahiye'}), 400

    eid = run("""
        INSERT INTO extra_money (worker_id, month_label, month_year, amount, reason)
        VALUES (?,?,?,?,?)
    """, [worker_id, label, my or None, amount, reason])

    entry = qry("SELECT * FROM extra_money WHERE id=?", [eid], one=True)
    return jsonify({'success': True, 'entry': dict(entry)}), 201

@app.route('/api/extra_money/<int:eid>', methods=['DELETE'])
def api_delete_extra(eid):
    e = qry("SELECT id FROM extra_money WHERE id=?", [eid], one=True)
    if not e: return jsonify({'error': 'Entry nahi mili'}), 404
    run("DELETE FROM extra_money WHERE id=?", [eid])
    return jsonify({'success': True})

# ─────────────────────────────────────────────────────────────
#  PAYMENTS API
# ─────────────────────────────────────────────────────────────
@app.route('/api/payments', methods=['GET'])
def api_get_payments():
    wid = request.args.get('worker_id')
    my  = request.args.get('month_year')
    if wid and my:
        rows = qry("SELECT * FROM payments WHERE worker_id=? AND month_year=? ORDER BY payment_date DESC", [wid, my])
    elif wid:
        rows = qry("SELECT * FROM payments WHERE worker_id=? ORDER BY payment_date DESC", [wid])
    else:
        rows = qry("SELECT * FROM payments ORDER BY payment_date DESC LIMIT 100")
    return jsonify([dict(r) for r in rows])

@app.route('/api/payments', methods=['POST'])
def api_add_payment():
    d         = request.get_json() or {}
    worker_id = d.get('worker_id')
    my        = (d.get('month_year') or '').strip()
    amount    = float(d.get('amount') or 0)
    ptype     = d.get('payment_type', 'salary')
    pmode     = d.get('payment_mode', 'cash')
    notes     = (d.get('notes') or '').strip()
    pdate     = (d.get('payment_date') or date.today().isoformat()).strip()

    if not worker_id: return jsonify({'error': 'worker_id zaroori hai'}), 400
    if not my:        return jsonify({'error': 'month_year zaroori hai'}), 400
    if amount <= 0:   return jsonify({'error': 'Amount 0 se zyada hona chahiye'}), 400

    pid = run("""
        INSERT INTO payments (worker_id, month_year, amount, payment_type, payment_mode, payment_date, notes)
        VALUES (?,?,?,?,?,?,?)
    """, [worker_id, my, amount, ptype, pmode, pdate, notes])

    payment = qry("SELECT * FROM payments WHERE id=?", [pid], one=True)
    return jsonify({'success': True, 'payment': dict(payment)}), 201

# ─────────────────────────────────────────────────────────────
#  REGISTER — FULL PAGE DATA (single call)
# ─────────────────────────────────────────────────────────────
@app.route('/api/register/<month_year>', methods=['GET'])
def api_register(month_year):
    """
    Returns all workers with:
      - attendance dict  {day_str: status}  for the given month
      - extra_money list (ALL time, not just this month)
      - payments list    for this month
      - computed totals
    """
    try:
        y, m = map(int, month_year.split('-'))
        days_in_month = calendar.monthrange(y, m)[1]
    except Exception:
        return jsonify({'error': 'month_year format galat hai'}), 400

    workers = qry("""
        SELECT * FROM workers
        WHERE is_active = 1
        ORDER BY role, full_name
    """)

    # Bulk-load all attendance for this month (one query)
    att_rows = qry("""
        SELECT worker_id, day_number, status
        FROM   attendance
        WHERE  month_year = ?
    """, [month_year])
    att_map = {}  # {worker_id: {day_str: status}}
    for r in att_rows:
        att_map.setdefault(r['worker_id'], {})[str(r['day_number'])] = r['status']

    # Bulk-load extra money for all active workers
    extra_rows = qry("""
        SELECT em.* FROM extra_money em
        JOIN   workers w ON w.id = em.worker_id
        WHERE  w.is_active = 1
        ORDER  BY em.month_year DESC, em.created_at DESC
    """)
    extra_map = {}  # {worker_id: [entries]}
    for r in extra_rows:
        extra_map.setdefault(r['worker_id'], []).append(dict(r))

    # Bulk-load payments for this month
    pay_rows = qry("""
        SELECT p.* FROM payments p
        JOIN   workers w ON w.id = p.worker_id
        WHERE  p.month_year = ? AND w.is_active = 1
        ORDER  BY p.payment_date DESC
    """, [month_year])
    pay_map = {}  # {worker_id: [payments]}
    for r in pay_rows:
        pay_map.setdefault(r['worker_id'], []).append(dict(r))

    result = []
    for w in workers:
        wid  = w['id']
        att  = att_map.get(wid, {})
        exts = extra_map.get(wid, [])
        pays = pay_map.get(wid, [])

        # Compute attendance totals for this month
        total_days = sum(
            STATUS_VALUE.get(att.get(str(d), ''), 0.0)
            for d in range(1, days_in_month + 1)
        )
        monthly_pay   = round(total_days * w['daily_rate'], 2)
        extra_total   = round(sum(e['amount'] for e in exts), 2)
        paid_total    = round(sum(p['amount'] for p in pays
                                  if p['payment_type'] != 'deduction'), 2)
        balance_due   = round(monthly_pay + extra_total - paid_total, 2)
        current_total = round(monthly_pay + extra_total, 2)

        result.append({
            **dict(w),
            'attendance':   att,
            'extra_money':  exts,
            'payments':     pays,
            'total_days':   total_days,
            'monthly_pay':  monthly_pay,
            'extra_total':  extra_total,
            'paid_total':   paid_total,
            'balance_due':  balance_due,
            'current_total': current_total,
        })

    return jsonify(result)

# ─────────────────────────────────────────────────────────────
#  STATS API
# ─────────────────────────────────────────────────────────────
@app.route('/api/stats/<month_year>', methods=['GET'])
def api_stats(month_year):
    today = date.today().isoformat()

    total_workers = qry(
        "SELECT COUNT(*) c FROM workers WHERE is_active=1", one=True)['c']

    present_today = qry(
        "SELECT COUNT(*) c FROM attendance WHERE att_date=? AND status='P'",
        [today], one=True)['c']

    row = qry("""
        SELECT COALESCE(SUM(a.day_value * w.daily_rate), 0) total
        FROM   attendance a JOIN workers w ON w.id=a.worker_id
        WHERE  a.month_year=? AND w.is_active=1
    """, [month_year], one=True)
    monthly_pay = round(row['total'], 2)

    row2 = qry("""
        SELECT COALESCE(SUM(em.amount), 0) total
        FROM   extra_money em JOIN workers w ON w.id=em.worker_id
        WHERE  w.is_active=1
    """, one=True)
    extra_total = round(row2['total'], 2)

    row3 = qry("""
        SELECT COALESCE(SUM(amount), 0) total
        FROM   payments
        WHERE  month_year=? AND payment_type != 'deduction'
    """, [month_year], one=True)
    paid_total = round(row3['total'], 2)

    # months that have ANY attendance data
    months = qry("""
        SELECT DISTINCT month_year
        FROM   attendance
        ORDER  BY month_year DESC
    """)

    return jsonify({
        'total_workers': total_workers,
        'present_today': present_today,
        'monthly_pay':   monthly_pay,
        'extra_total':   extra_total,
        'current_total': round(monthly_pay + extra_total, 2),
        'paid_total':    paid_total,
        'balance_due':   round(monthly_pay + extra_total - paid_total, 2),
        'active_months': [r['month_year'] for r in months],
    })

# ─────────────────────────────────────────────────────────────
#  HISTORY — months that have data for a worker
# ─────────────────────────────────────────────────────────────
@app.route('/api/worker_months/<int:wid>', methods=['GET'])
def api_worker_months(wid):
    months = qry("""
        SELECT DISTINCT month_year FROM attendance
        WHERE worker_id=?
        UNION
        SELECT DISTINCT month_year FROM payments
        WHERE worker_id=? AND month_year IS NOT NULL
        ORDER BY month_year DESC
    """, [wid, wid])
    return jsonify([r['month_year'] for r in months])

# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("🚀  Open browser: http://127.0.0.1:5000")
    print("    Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
