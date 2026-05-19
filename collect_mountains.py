
import requests
import sqlite3

SPARQL_URL = "https://query.wikidata.org/sparql"
QUERY = """
SELECT ?item ?itemLabel ?elevation WHERE {
    ?item wdt:P31 wd:Q8502.
    ?item wdt:P17 wd:Q17.
    OPTIONAL { ?item wdt:P2044 ?elevation. }
    SERVICE wikibase:label { bd:serviceParam wikibase:language "ja,en". }
    }
    LIMIT 50
    """

def fetch_mountains():
    res = requests.get(SPARQL_URL, params={"query": QUERY, "format": "json"}, headers={"Accept": "application/json", "User-Agent": "AI-SAN/1.0 (higaki@example.com)"})
    return res.json()["results"]["bindings"]

def save_to_db(mountains):
    conn = sqlite3.connect("ai_san.db")
    cur = conn.cursor()
    count = 0
    for m in mountains:
        name = m.get("itemLabel", {}).get("value", "")
        elevation = m.get("elevation", {}).get("value", None)
        if elevation:
            elevation = float(elevation)
        if not name or name.startswith("Q"):
            continue
        cur.execute("INSERT INTO mountains (name, region, elevation, forest_type, created_at) VALUES (?, ?, ?, ?, '2026-05-19')", (name, "日本", elevation, "未分類"))
        count += 1
    conn.commit()
    conn.close()
    print(f"{count}件登録完了")

if __name__ == "__main__":
    print("取得中...")
    mountains = fetch_mountains()
    save_to_db(mountains)

