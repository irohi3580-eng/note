import sqlite3
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret_key"

def get_db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS memos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        user_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ログインチェック
def login_required():
    if "user_id" not in session:
        return False
    return True

# トップ（メモ一覧）
@app.route("/")
def index():
    if not login_required():
        return redirect("/login")

    conn = get_db()
    memos = conn.execute(
        "SELECT * FROM memos WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("index.html", memos=memos)

# メモ追加
@app.route("/add", methods=["POST"])
def add():
    if not login_required():
        return redirect("/login")

    content = request.form["content"]

    conn = get_db()
    conn.execute(
        "INSERT INTO memos (content, user_id) VALUES (?, ?)",
        (content, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect("/")

# 登録
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except:
            return "ユーザー名は既に使われています"

        conn.close()
        return redirect("/login")

    return render_template("register.html")

# ログイン
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        # エラーを渡す
        if not user or not check_password_hash(user["password"], password):
            return render_template(
                "login.html",
                error="ユーザー名またはパスワードが違います"
            )

        # 成功
        session["user_id"] = user["id"]
        return redirect("/")

    return render_template("login.html")

    return render_template("login.html")

# ログアウト
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# 削除
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM memos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# 編集画面
@app.route("/edit/<int:id>")
def edit(id):
    conn = get_db()
    memo = conn.execute("SELECT * FROM memos WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("edit.html", memo=memo)

# 更新処理
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    content = request.form["content"]

    conn = get_db()
    conn.execute("UPDATE memos SET content = ? WHERE id = ?", (content, id))
    conn.commit()
    conn.close()

    return redirect("/")

app.run(debug=True)