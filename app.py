import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "my_secret_key_1234" # 보안용 키 (아무 문자나 가능)

# --- 데이터베이스 연결 함수 ---
def get_db_connection():
    # database.db 파일에 연결합니다.
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- 서버 시작 시 데이터베이스 초기화 ---
def init_db():
    conn = get_db_connection()
    # posts 테이블이 없으면 새로 만듭니다 (id, 작성자, 내용)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 임시 회원 목록 (나중에 회원가입 기능을 만들면 DB로 옮길 수 있어요!)
users = {
    "test@email.com": "1234",
    "admin": "1234",
    "friend": "0000"
}

# --- 페이지 경로 설정 ---

# 1. 메인 페이지 (로그인 화면)
@app.route('/')
def home():
    return render_template('index.html')

# 2. 로그인 처리
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    pwd = request.form.get('password')
    
    if email in users and users[email] == pwd:
        # 로그인 성공 시 게시판으로 이동 (사용자 이름을 주소에 담아 보냄)
        return redirect(url_for('board', user_email=email))
    else:
        return "<h1>로그인 정보가 틀렸습니다!</h1><a href='/'>다시 시도</a>"

# 3. 게시판 페이지 (피드 보기)
@app.route('/board')
def board():
    user_email = request.args.get('user_email')
    
    # DB에서 모든 글을 가져와서 최신순(id 역순)으로 정렬
    conn = get_db_connection()
    db_posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    
    return render_template('board.html', user=user_email, all_posts=db_posts)

# 4. 글쓰기 처리
@app.route('/write', methods=['POST'])
def write():
    user_email = request.form.get('user')
    content = request.form.get('content')
    
    if content:
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user, content) VALUES (?, ?)', (user_email, content))
        conn.commit()
        conn.close()
    
    return redirect(url_for('board', user_email=user_email))

# --- 서버 실행 설정 (외부 접속 허용) ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
