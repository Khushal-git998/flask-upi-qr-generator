from flask import Flask, render_template, request, send_file, redirect
import qrcode
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

QR_PATH = "payment_qr.png"
DB_PATH = "transactions.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upi_id TEXT,
            name TEXT,
            amount TEXT,
            note TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT upi_id, name, amount, note, timestamp FROM history ORDER BY id DESC")
    history = cur.fetchall()
    conn.close()

    preview = {
        "name": "—",
        "amount": "0",
        "note": "None"
    }

    return render_template("index.html", history=history, preview=preview)


@app.route("/generate", methods=["POST"])
def generate_qr():
    upi_id = request.form["upi"]
    name = request.form["name"]
    amount = request.form["amount"]
    note = request.form["note"]

    payload = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR&tn={note}"

    img = qrcode.make(payload)
    img.save(QR_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (upi_id, name, amount, note, timestamp) VALUES (?, ?, ?, ?, ?)",
        (upi_id, name, amount, note, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return render_template("index.html", history=get_history(), preview={
        "name": name,
        "amount": amount,
        "note": note if note else "None"
    })


def get_history():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT upi_id, name, amount, note, timestamp FROM history ORDER BY id DESC")
    history = cur.fetchall()
    conn.close()
    return history


@app.route("/qr_image")
def qr_image():
    if os.path.exists(QR_PATH):
        return send_file(QR_PATH)
    return ""


@app.route("/download")
def download_qr():
    return send_file(QR_PATH, as_attachment=True)


if __name__ == "__main__":
    # IMPORTANT: host=0.0.0.0 allows access from other devices
    app.run(host="0.0.0.0", port=5000, debug=False)
