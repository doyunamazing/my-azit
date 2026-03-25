import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_key_1234"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 유저 테이블
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)')
    # 게시글 테이블 (created_at 포함)
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, content TEXT, created_at TEXT)')
    # ⭐ 좋아요 테이블 추가 (누가 어느 글에 좋아요를 눌렀는지 저장)
    conn.execute('CREATE TABLE IF NOT EXISTS likes (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, post_id INTEGER)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user' in session: # 이미 로그인 상태면 게시판으로
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
        session.clear() # 기존 세션 깨끗이 비우기
        session['user'] = email
        return redirect(url_for('board'))
    return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.'); history.back();</script>"

@app.route('/board')
def board():
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    # 게시글을 가져오면서 각 글의 좋아요 개수도 함께 가져옵니다.
    posts_data = conn.execute('SELECT *, (SELECT COUNT(*) FROM likes WHERE post_id = posts.id) as like_count FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('board.html', user=session['user'], all_posts=posts_data)

@app.route('/write', methods=['POST'])
def write():
    content = request.form.get('content')
    if content and 'user' in session:
        now = datetime.now().strftime('%m-%d %H:%M')
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user, content, created_at) VALUES (?, ?, ?)', (session['user'], content, now))
        conn.commit()
        conn.close()
    return redirect(url_for('board'))

# ⭐ 좋아요 기능 라우트
@app.route('/like/<int:post_id>')
def like(post_id):
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    # 이미 좋아요를 눌렀는지 확인
    already_liked = conn.execute('SELECT * FROM likes WHERE user = ? AND post_id = ?', (session['user'], post_id)).fetchone()
    if already_liked:
        conn.execute('DELETE FROM likes WHERE user = ? AND post_id = ?', (session['user'], post_id)) # 좋아요 취소
    else:
        conn.execute('INSERT INTO likes (user, post_id) VALUES (?, ?)', (session['user'], post_id)) # 좋아요 추가
    conn.commit()
    conn.close()
    return redirect(url_for('board'))

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if 'user' not in session: return redirect(url_for('home'))
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ? AND user = ?', (post_id, session['user']))
    conn.execute('DELETE FROM likes WHERE post_id = ?', (post_id,)) # 글 삭제 시 좋아요 데이터도 삭제
    conn.commit()
    conn.close()
    return redirect(url_for('board'))

@app.route('/logout')
def logout():
    session.clear() # 세션 완전히 비우기
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
