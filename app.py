from flask import Flask, render_template, request, redirect, session
from blockchain import Blockchain
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'secret123'

blockchain = Blockchain()

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)')
    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?)", (user, password))
        conn.commit()
        conn.close()

        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, password))
        result = c.fetchone()
        conn.close()

        if result:
            session['user'] = user
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        file = request.files.get('file')

        if file and file.filename != "":
            # create uploads folder if not exists
            if not os.path.exists("uploads"):
                os.makedirs("uploads")

            filepath = os.path.join("uploads", file.filename)
            file.save(filepath)

            # Generate file hash
            with open(filepath, "rb") as f:
                file_data = f.read()
                file_hash = hashlib.sha256(file_data).hexdigest()

            previous_block = blockchain.get_previous_block()
            proof = blockchain.proof_of_work(previous_block['proof'])
            previous_hash = blockchain.hash(previous_block)

            blockchain.create_block(proof, previous_hash, file_hash)

    return render_template('dashboard.html', chain=blockchain.chain)


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    result = None

    if request.method == 'POST':
        file = request.files.get('file')

        if file and file.filename != "":
            # ensure uploads folder exists
            if not os.path.exists("uploads"):
                os.makedirs("uploads")

            filepath = os.path.join("uploads", file.filename)
            file.save(filepath)

            # Generate hash
            with open(filepath, "rb") as f:
                file_data = f.read()
                file_hash = hashlib.sha256(file_data).hexdigest()

            # Check blockchain
            found = any(block['data'] == file_hash for block in blockchain.chain)

            if found:
                result = "✅ File is ORIGINAL (not tampered)"
            else:
                result = "❌ File is TAMPERED"

    return render_template('verify.html', result=result)


if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True)