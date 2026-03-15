"""
OSINT X Scraper — GitHub Actions
Utilise Apify kaitoeasyapi via API
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────
# COMPTES À SURVEILLER
# ─────────────────────────────────────────
ACCOUNTS = [
    "EliasuAlhaji", "secmxx", "DanKatsina50", "TracTerrorism",
    "KargnHasret", "ighazer", "fabsenbln", "TchadOne",
    "aboub_Assikabar", "BrantPhilip_", "abousaib", "EyeonMali",
    "Youss2Bouna", "HumanityPurpose", "Intelligency225", "SahelLeaks",
    "ZagazOlaMakama", "MedLilly1", "hamid_gade", "AgAnchawadje",
    "mintelworld", "malkoomx00", "michombero", "Malijetactu"
]

MAX_ITEMS    = 100
HOURS_LOOKBACK = 36
ACTOR_ID     = "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest"

# ─────────────────────────────────────────

def main():
    # Debug : afficher toutes les variables d'environnement liées
    token = os.environ.get("APIFY_TOKEN", "")
    print(f"DEBUG : APIFY_TOKEN présent = {bool(token)}, longueur = {len(token)}")
    print(f"DEBUG : Variables env disponibles = {[k for k in os.environ if 'APIFY' in k.upper()]}")

    if not token:
        print("ERREUR : Variable APIFY_TOKEN manquante dans les secrets GitHub")
        sys.exit(1)

    search_query = " OR ".join(f"from:{acc}" for acc in ACCOUNTS)
    print(f"Query : {search_query[:80]}...")

    def apify_req(method, path, data=None):
        url = f"https://api.apify.com/v2{path}?token={token}"
        body = json.dumps(data).encode() if data else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    print("Lancement du Run Apify...")
    run = apify_req("POST", f"/acts/{ACTOR_ID}/runs", {
        "searchTerms": [search_query],
        "maxItems": MAX_ITEMS,
        "queryType": "Latest"
    })
    run_id = run["data"]["id"]
    print(f"Run ID : {run_id}")

    for _ in range(60):
        time.sleep(5)
        status = apify_req("GET", f"/actor-runs/{run_id}")
        st = status["data"]["status"]
        print(f"  Statut : {st}")
        if st in ("SUCCEEDED", "FAILED", "ABORTED"):
            break

    if st != "SUCCEEDED":
        print(f"ERREUR : Run terminé avec statut {st}")
        sys.exit(1)

    dataset_id = status["data"]["defaultDatasetId"]
    print(f"Dataset ID : {dataset_id}")

    items_resp = apify_req("GET", f"/datasets/{dataset_id}/items")
    items = items_resp if isinstance(items_resp, list) else items_resp.get("items", [])
    print(f"{len(items)} tweets récupérés")

    since_dt = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    tweets = []
    for i, item in enumerate(items):
        raw = item.get("full_text") or item.get("text") or item.get("tweetText") or ""
        if not raw:
            continue
        created = item.get("createdAt") or item.get("created_at") or ""
        try:
            tweet_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except Exception:
            tweet_dt = datetime.now(timezone.utc)
        if tweet_dt < since_dt:
            continue
        author = ""
        if item.get("author"):
            author = "@" + (item["author"].get("userName") or item["author"].get("screen_name") or "")
        elif item.get("user"):
            author = "@" + (item["user"].get("screen_name") or "")
        media_url = ""
        if item.get("media") and len(item["media"]) > 0:
            media_url = item["media"][0].get("media_url_https") or item["media"][0].get("url") or ""
        tweets.append({
            "id": i, "src": "X", "acc": author,
            "time": tweet_dt.strftime("%H:%M"),
            "date_in": tweet_dt.strftime("%Y-%m-%d"),
            "url": item.get("url") or item.get("tweetUrl") or "#",
            "mediaUrl": media_url, "raw": raw,
            "selected": False, "llm_done": False, "status": "pending", "desc": "",
            "fields": {"ctrl":"","date":"","pays":"","reg":"","ville":"",
                      "lat":"","lon":"","acteur":"","type":"","media":"","conf":{}}
        })

    tweets.sort(key=lambda x: x["date_in"] + x["time"], reverse=True)
    for i, t in enumerate(tweets):
        t["id"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accounts": ACCOUNTS, "total": len(tweets), "tweets": tweets
    }
    with open("tweets.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✓ {len(tweets)} tweets écrits dans tweets.json")

if __name__ == "__main__":
    main()
