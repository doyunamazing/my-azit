import os
import sqlite3
from datetime import datetime # 시간 계산용
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_key_1234"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 데이터베이스 초기화 (시간 저장용 created_at 칸 추가)
def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, content TEXT, created_at TEXT)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    pwd = request.form.get('password')
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, pwd))
        conn.commit()
        conn.close()
        return "<script>alert('가입 완료! 로그인 해주세요.'); location.href='/';</script>"
    except:
        return "<script>alert('이미 있는 아이디입니다.'); history.back();</script>"

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    pwd = request.form.get('password')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, pwd)).fetchone()
    conn.close()
    if user:
        session['user'] = email
        return redirect(url_for('board'))
    return "<script>alert('로그인 실패!'); history.back();</script>"

@app.route('/board')
def board():
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    db_posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('board.html', user=session['user'], all_posts=db_posts)

@app.route('/write', methods=['POST'])
def write():
    content = request.form.get('content')
    if content and 'user' in session:
        now = datetime.now().strftime('%m-%d %H:%M') # "월-일 시:분" 형식
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user, content, created_at) VALUES (?, ?, ?)', 
                     (session['user'], content, now))
        conn.commit()
        conn.close()
    return redirect(url_for('board'))

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ? AND user = ?', (post_id, session['user']))
    conn.commit()
    conn.close()
    return redirect(url_for('board'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
