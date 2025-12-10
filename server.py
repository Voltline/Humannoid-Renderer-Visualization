from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, static_folder="static")
CORS(app)

# =======================================================
# SQLite 初始化
# =======================================================

DB_PATH = "poses.db"

def init_db():
    """Create table if not exists"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS poses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            px REAL NOT NULL,
            py REAL NOT NULL,
            pz REAL NOT NULL,
            qx REAL NOT NULL,
            qy REAL NOT NULL,
            qz REAL NOT NULL,
            qw REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

# =======================================================
# In-memory buffer（保留你的机制）
# =======================================================
pose_buffer = []

# =======================================================
# API 1: 接收姿态数据 /pose
# =======================================================
@app.post("/pose")
def post_pose():
    data = request.get_json()

    # Basic validation
    if not data or "timestamp" not in data or "position" not in data or "quaternion" not in data:
        return jsonify({"error": "Invalid pose format"}), 400

    pose_buffer.append(data)

    # Save to SQLite
    pos = data["position"]
    quat = data["quaternion"]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO poses(timestamp, px, py, pz, qx, qy, qz, qw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (data["timestamp"], pos[0], pos[1], pos[2], quat[0], quat[1], quat[2], quat[3]),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


# =======================================================
# API 2: 获取轨迹 /trajectory
# =======================================================
@app.get("/trajectory")
def get_trajectory():

    # 如果你想仅取内存，可保持 pose_buffer
    # 但这里同步数据库，让前端永远能获取完整持久化数据

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT timestamp, px, py, pz, qx, qy, qz, qw FROM poses")
    rows = cur.fetchall()
    conn.close()

    result = [
        {
            "timestamp": r[0],
            "position": [r[1], r[2], r[3]],
            "quaternion": [r[4], r[5], r[6], r[7]],
        }
        for r in rows
    ]

    return jsonify(result)


# =======================================================
# API 3: 清空数据 /clear
# =======================================================
@app.post("/clear")
def clear_data():

    # 清空内存
    pose_buffer.clear()

    # 清空数据库
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM poses")
    conn.commit()
    conn.close()

    return jsonify({"status": "cleared"})


# =======================================================
# 静态页面
# =======================================================
@app.get("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/replay")
def serve_replay():
    return send_from_directory(app.static_folder, "replay.html")


@app.get("/<path:path>")
def serve_static_file(path):
    return send_from_directory(app.static_folder, path)


# =======================================================
# 启动服务
# =======================================================
if __name__ == "__main__":
    print("🚀 Vision Pro server is running at http://localhost:30000")
    app.run(host="0.0.0.0", port=30000, debug=False)