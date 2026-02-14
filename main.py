from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import sqlite3
from datetime import datetime

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

        conn.close()

        self.ids.stats.text = f"عدد المرضى: {patients}\nعدد الزيارات: {visits}\nإجمالي الأرباح: {total}"


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

        c.execute("INSERT INTO visits (patient_id, date, price, paid) VALUES (?,?,?,?)",
                  (pid, datetime.now().strftime("%Y-%m-%d"), price, paid))

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
            text += f"{r[0]} - {r[1]} - {r[2]} - {r[3]}\n"

        self.ids.results.text = text or "لا يوجد نتائج"


class WindowManager(ScreenManager):
    pass


class ClinicApp(App):
    def build(self):
        init_db()
        return WindowManager()


if __name__ == "__main__":
    ClinicApp().run()
