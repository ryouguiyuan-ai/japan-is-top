import re
import sqlite3

import requests

SPARQL_URL = "https://query.wikidata.org/sparql"
# Wikidata: identify your client (https://wikidata.wikimedia.org/wiki/Wikidata:Data_access)
USER_AGENT = (
    "AI-SAN/1.0 (https://github.com/ryouguiyuan-ai/japan-is-top; "
    "wikidata-import)"
)
HEADERS = {
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
}

TARGET_COUNT = 2000
PAGE_SIZE = 500

POINT_RE = re.compile(r"^Point\(([-\d.]+)\s+([-\d.]+)\)$")


def parse_point(wkt: str | None) -> tuple[float | None, float | None]:
    """WKT Point(longitude latitude) -> (latitude, longitude)."""
    if not wkt:
        return None, None
    match = POINT_RE.match(wkt.strip())
    if not match:
        return None, None
    longitude = float(match.group(1))
    latitude = float(match.group(2))
    return latitude, longitude


def ensure_schema(cur: sqlite3.Cursor) -> None:
    cur.execute("PRAGMA table_info(mountains)")
    cols = {row[1] for row in cur.fetchall()}
    if "latitude" not in cols:
        cur.execute("ALTER TABLE mountains ADD COLUMN latitude REAL")
    if "longitude" not in cols:
        cur.execute("ALTER TABLE mountains ADD COLUMN longitude REAL")


def sparql_query(limit: int, offset: int) -> str:
    """One row per mountain (GROUP BY); labels ja,en; optional coords."""
    return f"""
SELECT ?item ?itemLabel ?elevation ?coord WHERE {{
  {{
    SELECT ?item (SAMPLE(?elev) AS ?elevation) (SAMPLE(?coordRaw) AS ?coord) WHERE {{
      ?item wdt:P31 wd:Q8502.
      ?item wdt:P17 wd:Q17.
      OPTIONAL {{ ?item wdt:P2044 ?elev. }}
      OPTIONAL {{ ?item wdt:P625 ?coordRaw. }}
    }}
    GROUP BY ?item
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}
ORDER BY ?item
LIMIT {limit}
OFFSET {offset}
"""


def fetch_bindings(limit: int, offset: int) -> list:
    query = sparql_query(limit, offset)
    res = requests.get(
        SPARQL_URL,
        params={"query": query, "format": "json"},
        headers=HEADERS,
        timeout=180,
    )
    res.raise_for_status()
    return res.json()["results"]["bindings"]


def save_batch(
    cur,
    mountains: list,
    seen_items: set,
    max_insert: int | None = None,
) -> int:
    """Insert new rows; skip duplicate ?item URIs and invalid labels."""
    count = 0
    for m in mountains:
        if max_insert is not None and count >= max_insert:
            break
        item_uri = m.get("item", {}).get("value", "")
        if not item_uri or item_uri in seen_items:
            continue
        name = m.get("itemLabel", {}).get("value", "")
        elevation_raw = m.get("elevation", {}).get("value", None)
        elevation = None
        if elevation_raw is not None:
            try:
                elevation = float(elevation_raw)
            except (TypeError, ValueError):
                elevation = None
        coord_raw = m.get("coord", {}).get("value", None)
        latitude, longitude = parse_point(coord_raw)
        if not name or name.startswith("Q"):
            continue
        seen_items.add(item_uri)
        cur.execute(
            "INSERT INTO mountains "
            "(name, region, elevation, latitude, longitude, forest_type, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, date('now'))",
            (name, "日本", elevation, latitude, longitude, "未分類"),
        )
        count += 1
    return count


def main() -> None:
    conn = sqlite3.connect("ai_san.db")
    cur = conn.cursor()
    ensure_schema(cur)
    cur.execute("DELETE FROM mountains")
    conn.commit()
    print("既存の mountains データを削除しました")

    seen_items: set[str] = set()
    total_inserted = 0
    offset = 0
    print("取得中...")
    while total_inserted < TARGET_COUNT:
        batch = fetch_bindings(PAGE_SIZE, offset)
        if not batch:
            break
        remaining = TARGET_COUNT - total_inserted
        added = save_batch(cur, batch, seen_items, remaining)
        total_inserted += added
        offset += PAGE_SIZE
        conn.commit()
        print(f"累計 {total_inserted} / {TARGET_COUNT} 件（次オフセット {offset}）")
        if total_inserted >= TARGET_COUNT or len(batch) < PAGE_SIZE:
            break
    conn.close()
    print(f"{total_inserted}件登録完了")


if __name__ == "__main__":
    main()
