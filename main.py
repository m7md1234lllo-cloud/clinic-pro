from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os

DB = "clinic.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        date TEXT,
        price REAL,
        paid REAL
    )
    """)

    conn.commit()
    conn.close()


# ---------------- Dashboard ----------------

class Dashboard(Screen):
    def on_enter(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM patients")
        patients = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM visits")
        visits = c.fetchone()[0]

        c.execute("SELECT SUM(price) FROM visits")
        total = c.fetchone()[0] or 0

        c.execute("SELECT SUM(price - paid) FROM visits")
        debts = c.fetchone()[0] or 0

        conn.close()

        self.ids.stats.text = (
            f"عدد المرضى: {patients}\n"
            f"عدد الزيارات: {visits}\n"
            f"إجمالي الأرباح: {total}\n"
            f"إجمالي الديون: {debts}"
        )


# ---------------- Add Visit ----------------

class AddVisit(Screen):
    def save(self):
        name = self.ids.name.text
        price = float(self.ids.price.text or 0)
        paid = float(self.ids.paid.text or 0)

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT id FROM patients WHERE name=?", (name,))
        patient = c.fetchone()

        if patient:
            pid = patient[0]
        else:
            c.execute("INSERT INTO patients (name) VALUES (?)", (name,))
            pid = c.lastrowid

        c.execute("""
        INSERT INTO visits (patient_id, date, price, paid)
        VALUES (?, ?, ?, ?)
        """, (pid, datetime.now().strftime("%Y-%m-%d"), price, paid))

        conn.commit()
        conn.close()

        self.ids.result.text = f"المتبقي: {price - paid}"


# ---------------- Search ----------------

class Search(Screen):
    def search(self):
        name = self.ids.search_name.text

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
        SELECT patients.name, visits.date, visits.price, visits.paid
        FROM visits
        JOIN patients ON visits.patient_id = patients.id
        WHERE patients.name LIKE ?
        """, (f"%{name}%",))

        results = c.fetchall()
        conn.close()

        text = ""
        for r in results:
            remaining = r[2] - r[3]
            text += f"{r[0]} | {r[1]} | المتبقي: {remaining}\n"

        self.ids.results.text = text or "لا يوجد نتائج"


# ---------------- Debts ----------------

class Debts(Screen):
    def on_enter(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
        SELECT patients.name, visits.date, (price - paid)
        FROM visits
        JOIN patients ON visits.patient_id = patients.id
        WHERE price > paid
        """)

        results = c.fetchall()
        conn.close()

        text = ""
        for r in results:
            text += f"{r[0]} | {r[1]} | دين: {r[2]}\n"

        self.ids.debts_label.text = text or "لا يوجد ديون"


# ---------------- PDF ----------------

class PDF(Screen):
    def generate(self):
        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
        SELECT patients.name, visits.date, visits.price, visits.paid
        FROM visits
        JOIN patients ON visits.patient_id = patients.id
        """)

        data = c.fetchall()
        conn.close()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        pdf.cell(200, 10, txt="Clinic Report", ln=True)

        for row in data:
            remaining = row[2] - row[3]
            pdf.cell(200, 8,
                     txt=f"{row[0]} | {row[1]} | {remaining}",
                     ln=True)

        pdf.output("clinic_report.pdf")
        self.ids.msg.text = "تم إنشاء PDF"


class WindowManager(ScreenManager):
    pass


class ClinicApp(App):
    def build(self):
        init_db()
        return WindowManager()


if __name__ == "__main__":
    ClinicApp().run()
