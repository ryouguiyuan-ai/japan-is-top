import json
import sqlite3

from flask import Flask, jsonify, render_template

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


def get_db():
    conn = sqlite3.connect("ai_san.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return "AI-SAN API 稼働中"


@app.route("/mountains")
def mountains():
    conn = get_db()
    rows = conn.execute("SELECT * FROM mountains").fetchall()
    conn.close()
    return app.response_class(
        json.dumps([dict(r) for r in rows], ensure_ascii=False),
        mimetype="application/json",
    )


@app.route("/api/mountains")
def api_mountains():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM mountains "
        "WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/map")
def map_page():
    return render_template("map.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
