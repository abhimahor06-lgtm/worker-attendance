# 🏗️ CONTRACTOR REGISTER APP
### Thekedaar Panel — Flask + SQLite + Dynamic HTML
---

## ⚡ CHALANE KE STEPS

### Windows Users:
```
START_KARO.bat  ←  Double-click karo  ✅  (sab automatic)
```

### Manual Steps:
```bash
# 1. Folder mein jao
cd construction-app

# 2. Flask install karo (sirf ek baar)
pip install Flask

# 3. App chalu karo
python app.py

# 4. Browser mein kholo
http://127.0.0.1:5000
```

---

## ✅ FEATURES

| Feature | Kya hota hai |
|---------|-------------|
| Worker Add/Edit/Delete | Modal se real data — instantly database save |
| Attendance Toggle | Day cell click → P→A→H→HD→Clear — auto DB save |
| Month/Year Switch | Kisi bhi mahine ka data dekhó — PERMANENTLY saved |
| Months Bar | Hero mein orange chips — click karo kisi bhi past month |
| Extra Money | Per worker past months ka bonus — add/delete |
| Payment Track | Salary/Advance/Bonus record karo per month |
| Balance Due | Auto-calculate: Income - Paid = Due |
| Live Stats | Workers, Present Today, Monthly Pay, Extra, Balance, Total |
| Search | Name / mobile / role se filter |
| Export CSV | Poora register CSV mein download |
| History | Kisi bhi purane mahine ki attendance/payment kabhi bhi dekho |

---

## 📊 ATTENDANCE STATUS CODES

| Code | Matlab | Color |
|------|--------|-------|
| P  | Present — Full Day  (1 din)    | 🟢 Green |
| A  | Absent  — 0 din               | 🔴 Red   |
| H  | Half Day — 0.5 din            | 🟡 Amber |
| HD | Holiday — Paid (1 din)        | 🔵 Blue  |

---

## 📁 FOLDER STRUCTURE
```
construction-app/
├── app.py              ← Flask backend + database + APIs
├── requirements.txt    ← Flask only
├── START_KARO.bat      ← Windows double-click start
├── README.md
├── templates/
│   └── register.html   ← Full dynamic frontend
└── database/
    └── app.db          ← SQLite (auto-create)
```

---

## 🔗 API ENDPOINTS

| Method | URL | Kya karta hai |
|--------|-----|---------------|
| GET    | /api/workers              | Sare workers |
| POST   | /api/workers              | Add worker |
| PUT    | /api/workers/\<id\>       | Edit worker |
| DELETE | /api/workers/\<id\>       | Delete worker |
| POST   | /api/attendance           | Attendance mark/clear |
| GET    | /api/register/YYYY-MM     | Full page data |
| GET    | /api/stats/YYYY-MM        | Dashboard stats |
| POST   | /api/extra_money          | Extra entry add |
| DELETE | /api/extra_money/\<id\>   | Extra entry delete |
| POST   | /api/payments             | Payment record |

---

## 💾 DATABASE TABLES
```
workers       — Worker info (name, mobile, role, rate)
attendance    — Daily P/A/H/HD records  (YYYY-MM-DD)
extra_money   — Past month bonuses per worker
payments      — Salary/advance payments per month
```

---

## ❓ PROBLEM?

**Flask not found:**
```bash
pip install Flask
```

**Port already in use:**
```bash
python app.py  # already running hoga — band karo pehle
```

**Database error:**
```
database/ folder delete karo — auto ban jayega
```
