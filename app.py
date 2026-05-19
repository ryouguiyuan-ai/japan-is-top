from flask import Flask, jsonify
import sqlite3
import json

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
 return app.response_class(json.dumps([dict(r) for r in rows], ensure_ascii=False), mimetype="application/json")

if __name__ == "__main__":
 app.run(debug=True, port=5000)
