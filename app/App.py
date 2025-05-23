from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 雖然沒用 session 也先留著

DATABASE = 'membership.db'

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS members (
                iid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                phone TEXT,
                birthdate TEXT
            )
        ''')
        c.execute('''
            INSERT OR IGNORE INTO members (username, email, password, phone, birthdate)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@example.com', 'admin123', '0912345678', '1990-01-01'))
        conn.commit()
        conn.close()

@app.template_filter('add_stars')
def add_stars(s):
    return f'★{s}★'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        birthdate = request.form.get('birthdate', '').strip()

        if not username or not email or not password:
            return render_template('error.html', error='請輸入用戶名、電子郵件和密碼')

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('SELECT iid FROM members WHERE username = ?', (username,))
        if c.fetchone():
            conn.close()
            return render_template('error.html', error='用戶名已存在')

        c.execute('SELECT iid FROM members WHERE email = ?', (email,))
        if c.fetchone():
            conn.close()
            return render_template('error.html', error='電子郵件已註冊')

        c.execute('''
            INSERT INTO members (username, email, password, phone, birthdate)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password, phone, birthdate))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('error.html', error='請輸入電子郵件和密碼')

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT iid, username FROM members WHERE email = ? AND password = ?', (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            iid, username = user
            # 直接渲染歡迎頁，不用 session，iid 以參數帶給 welcome
            return redirect(url_for('welcome', iid=iid))
        else:
            return render_template('error.html', error='電子郵件或密碼錯誤')

    return render_template('login.html')

@app.route('/welcome/<int:iid>')
def welcome(iid):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT username FROM members WHERE iid = ?', (iid,))
    user = c.fetchone()
    conn.close()
    if not user:
        return render_template('error.html', error='找不到該用戶')
    username = user[0]
    return render_template('welcome.html', username=username, iid=iid)

@app.route('/edit_profile/<int:iid>', methods=['GET', 'POST'])
def edit_profile(iid):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        birthdate = request.form.get('birthdate', '').strip()

        if not email or not password:
            conn.close()
            return render_template('error.html', error='請輸入電子郵件和密碼')

        c.execute('SELECT iid FROM members WHERE email = ? AND iid != ?', (email, iid))
        if c.fetchone():
            conn.close()
            return render_template('error.html', error='電子郵件已被使用')

        c.execute('''
            UPDATE members SET email = ?, password = ?, phone = ?, birthdate = ? WHERE iid = ?
        ''', (email, password, phone, birthdate, iid))
        conn.commit()
        conn.close()
        return redirect(url_for('welcome', iid=iid))

    # GET 載入現有資料
    c.execute('SELECT username, email, password, phone, birthdate FROM members WHERE iid = ?', (iid,))
    member = c.fetchone()
    conn.close()
    if not member:
        return render_template('error.html', error='找不到該用戶')
    return render_template('edit_profile.html',
                           iid=iid,
                           username=member[0],
                           email=member[1],
                           password=member[2],
                           phone=member[3] or '',
                           birthdate=member[4] or '')

@app.route('/delete/<int:iid>', methods=['POST'])
def delete(iid):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('DELETE FROM members WHERE iid = ?', (iid,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

