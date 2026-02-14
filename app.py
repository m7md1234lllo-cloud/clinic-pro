from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "clinic.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        price REAL,
        paid REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        paid = float(request.form["paid"])

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO visits (name, date, price, paid) VALUES (?,?,?,?)",
                  (name, datetime.now().strftime("%Y-%m-%d"), price, paid))
        conn.commit()
        conn.close()

        return redirect("/")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM visits")
    visits = c.fetchall()
    conn.close()

    total = sum(v[3] for v in visits)
    debts = sum(v[3] - v[4] for v in visits)

    return render_template("index.html",
                           visits=visits,
                           total=total,
                           debts=debts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
