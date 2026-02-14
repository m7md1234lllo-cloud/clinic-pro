from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3, os, shutil
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)
DB_NAME = "clinic.db"

# ---------- إنشاء قاعدة البيانات ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    location TEXT
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER,
                    visit_date TEXT,
                    diagnosis TEXT,
                    notes TEXT
                )""")

    conn.commit()
    conn.close()

init_db()

# ---------- نسخ احتياطي ----------
def backup_database():
    if os.path.exists(DB_NAME):
        shutil.copy(DB_NAME, "backup.db")

# ---------- Dashboard ----------
@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM patients")
    patients_count = c.fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM visits WHERE visit_date=?", (today,))
    today_visits = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM visits")
    total_visits = c.fetchone()[0]

    conn.close()

    return render_template("dashboard.html",
                           patients_count=patients_count,
                           today_visits=today_visits,
                           total_visits=total_visits)

# ---------- إضافة زيارة ----------
@app.route("/add", methods=["GET", "POST"])
def add_visit():
    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        visit_date = request.form["visit_date"]
        diagnosis = request.form["diagnosis"]
        notes = request.form["notes"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("SELECT id FROM patients WHERE name=?", (name,))
        patient = c.fetchone()

        if patient:
            patient_id = patient[0]
        else:
            c.execute("INSERT INTO patients (name, location) VALUES (?,?)",
                      (name, location))
            patient_id = c.lastrowid

        c.execute("""INSERT INTO visits
                     (patient_id, visit_date, diagnosis, notes)
                     VALUES (?,?,?,?)""",
                     (patient_id, visit_date, diagnosis, notes))

        conn.commit()
        conn.close()

        backup_database()

        return redirect(url_for("dashboard"))

    return render_template("add.html")

# ---------- البحث ----------
@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        query = """SELECT patients.name, patients.location,
                          visits.visit_date, visits.diagnosis, visits.notes
                   FROM visits
                   JOIN patients ON visits.patient_id = patients.id
                   WHERE patients.name LIKE ? AND visits.visit_date LIKE ?"""

        c.execute(query, (f"%{name}%", f"%{date}%"))
        results = c.fetchall()
        conn.close()

    return render_template("search.html", results=results)

# ---------- إنشاء PDF ----------
@app.route("/pdf/<name>/<date>")
def generate_pdf(name, date):

    folder = f"patients/{name}"
    os.makedirs(folder, exist_ok=True)

    pdf_path = f"{folder}/visit_{date}.pdf"

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""SELECT patients.name, patients.location,
                        visits.visit_date, visits.diagnosis, visits.notes
                 FROM visits
                 JOIN patients ON visits.patient_id = patients.id
                 WHERE patients.name=? AND visits.visit_date=?""",
                 (name, date))

    data = c.fetchone()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Patient Medical File", ln=True)
    pdf.cell(200, 10, txt=f"Name: {data[0]}", ln=True)
    pdf.cell(200, 10, txt=f"Location: {data[1]}", ln=True)
    pdf.cell(200, 10, txt=f"Visit Date: {data[2]}", ln=True)
    pdf.cell(200, 10, txt=f"Diagnosis: {data[3]}", ln=True)
    pdf.multi_cell(0, 10, txt=f"Notes: {data[4]}")

    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
