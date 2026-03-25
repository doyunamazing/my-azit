import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = "azit_secret_key_999"
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
    if 'user' in session:
        return redirect(url_for('board'))
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
        return "<script>alert('가입 성공! 로그인해주세요.'); location.href='/';</script>"
    except:
        return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    pwd = request.form.get('password')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, pwd)).fetchone()
    conn.close()
    if user:
        session.permanent = True
        session['user'] = email
        return redirect(url_for('board'))
    return "<script>alert('아이디 또는 비번이 틀렸습니다.'); history.back();</script>"

@app.route('/board')
def board():
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    # 게시글 목록과 좋아요 정보 가져오기
    posts_data = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    
    final_posts = []
    for p in posts_data:
        p_dict = dict(p)
        likers = conn.execute('SELECT user FROM likes WHERE post_id = ?', (p['id'],)).fetchall()
        p_dict['like_count'] = len(likers)
        p_dict['liker_names'] = ", ".join([l['user'] for l in likers])
        final_posts.append(p_dict)
    
    conn.close()
    return render_template('board.html', user=session['user'], all_posts=final_posts)

@socketio.on('new_post')
def handle_new_post(data):
    if 'user' not in session: return
    content = data.get('content')
    if content:
        now = datetime.now().strftime('%m-%d %H:%M')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO posts (user, content, created_at) VALUES (?, ?, ?)', (session['user'], content, now))
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()
        emit('render_post', {'id': post_id, 'user': session['user'], 'content': content, 'created_at': now}, broadcast=True)

@socketio.on('like_post')
def handle_like(data):
    if 'user' not in session: return
    post_id = data.get('post_id')
    user = session['user']
    conn = get_db_connection()
    already = conn.execute('SELECT * FROM likes WHERE user = ? AND post_id = ?', (user, post_id)).fetchone()
    if already:
        conn.execute('DELETE FROM likes WHERE user = ? AND post_id = ?', (user, post_id))
    else:
        conn.execute('INSERT INTO likes (user, post_id) VALUES (?, ?)', (user, post_id))
    conn.commit()
    likers = conn.execute('SELECT user FROM likes WHERE post_id = ?', (post_id,)).fetchall()
    liker_list = [l['user'] for l in likers]
    conn.close()
    emit('update_likes', {'post_id': post_id, 'like_count': len(liker_list), 'likers': liker_list}, broadcast=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
