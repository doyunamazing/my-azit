import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit # 실시간 도구 추가

app = Flask(__name__)
app.secret_key = "secret_key_1234"
# 실시간 통신 엔진 설정
socketio = SocketIO(app, cors_allowed_origins="*")

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, content TEXT, created_at TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, post_id INTEGER)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user' in session: return redirect(url_for('board'))
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
        return "<script>alert('가입 완료!'); location.href='/';</script>"
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
        session.clear()
        session['user'] = email
        return redirect(url_for('board'))
    return "<script>alert('로그인 실패!'); history.back();</script>"

@app.route('/board')
def board():
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    posts_data = conn.execute('SELECT *, (SELECT COUNT(*) FROM likes WHERE post_id = posts.id) as like_count FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('board.html', user=session['user'], all_posts=posts_data)

# ⭐ 실시간 글쓰기 (기존 redirect 대신 socket으로 전송)
@socketio.on('new_post')
def handle_new_post(data):
    if 'user' not in session: return
    content = data.get('content')
    if content:
        now = datetime.now().strftime('%m-%d %H:%M')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (user, content, created_at) VALUES (?, ?, ?)', (session['user'], content, now))
        post_id = cursor.lastrowid # 방금 쓴 글의 번호
        conn.commit()
        conn.close()
        
        # 접속 중인 모든 사람에게 새 글 정보 전달
        emit('render_post', {
            'id': post_id,
            'user': session['user'],
            'content': content,
            'created_at': now,
            'like_count': 0
        }, broadcast=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
