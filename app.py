import json
import os
import sqlite3

from anthropic import Anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

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


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json(silent=True) or {}
    mood = data.get("mood", "").strip()
    if not mood:
        return jsonify({"error": "mood is required"}), 400

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY is not set"}), 500

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": (
                    f"日本の山で {mood} な気分の人におすすめの山を"
                    "1つ、150字以内で教えてください"
                ),
            }
        ],
    )
    recommendation = message.content[0].text
    return jsonify({"recommendation": recommendation})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
