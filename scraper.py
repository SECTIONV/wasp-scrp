"""
OSINT X Scraper — GitHub Actions
Scrape les tweets des comptes surveillés via snscrape (sans API X officielle)
Écrit le résultat dans tweets.json
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────
# COMPTES À SURVEILLER — modifiez cette liste
# ─────────────────────────────────────────
ACCOUNTS = [
"EliasuAlhaji",
"secmxx",
"DanKatsina50",
"TracTerrorism",
"KargnHasret",
"ighazer",
"fabsenbln",
"TchadOne",
"aboub_Assikabar",
"BrantPhilip_",
"abousaib",
"EyeonMali",
"Youss2Bouna",
"HumanityPurpose",
"Intelligency225",
"SahelLeaks",
"ZagazOlaMakama",
"MedLilly1",
"hamid_gade",
"AgAnchawadje",
"mintelworld",
"malkoomx00",
"michombero",
"Malijetactu",
]

# Nombre de tweets max par compte
MAX_TWEETS_PER_ACCOUNT = 20

# Ne garder que les tweets des dernières N heures
HOURS_LOOKBACK = 36

# ─────────────────────────────────────────

def install_deps():
    """Installe les dépendances si nécessaire"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "snscrape", "--quiet"])

def scrape_account(username, max_tweets, since_dt):
    """Scrape les tweets d'un compte via snscrape"""
    import snscrape.modules.twitter as sntwitter
    tweets = []
    try:
        scraper = sntwitter.TwitterUserScraper(username)
        for i, tweet in enumerate(scraper.get_items()):
            if i >= max_tweets * 3:  # marge de sécurité
                break
            # Filtrer par date
            tweet_dt = tweet.date.replace(tzinfo=timezone.utc) if tweet.date.tzinfo is None else tweet.date
            if tweet_dt < since_dt:
                break
            tweets.append({
                "id": str(tweet.id),
                "src": "X",
                "acc": "@" + username,
                "time": tweet_dt.strftime("%H:%M"),
                "date_in": tweet_dt.strftime("%Y-%m-%d"),
                "url": tweet.url,
                "mediaUrl": tweet.media[0].previewUrl if tweet.media else "",
                "raw": tweet.rawContent or tweet.content,
                "selected": False,
                "llm_done": False,
                "status": "pending",
                "desc": "",
                "fields": {
                    "ctrl": "", "date": "", "pays": "", "reg": "", "ville": "",
                    "lat": "", "lon": "", "acteur": "", "type": "", "media": "", "conf": {}
                }
            })
            if len(tweets) >= max_tweets:
                break
    except Exception as e:
        print(f"  Erreur sur @{username}: {e}")
    return tweets

def main():
    if not ACCOUNTS:
        print("ERREUR : Aucun compte défini dans ACCOUNTS. Modifiez le fichier scraper.py")
        sys.exit(1)

    print(f"Installation des dépendances...")
    install_deps()

    since_dt = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    all_tweets = []
    seen_ids = set()

    for username in ACCOUNTS:
        print(f"Scraping @{username}...")
        tweets = scrape_account(username, MAX_TWEETS_PER_ACCOUNT, since_dt)
        for t in tweets:
            if t["id"] not in seen_ids:
                seen_ids.add(t["id"])
                all_tweets.append(t)
        print(f"  → {len(tweets)} tweet(s)")

    # Trier par date décroissante
    all_tweets.sort(key=lambda x: x["date_in"] + x["time"], reverse=True)

    # Ajouter des IDs numériques uniques pour l'interface
    for i, t in enumerate(all_tweets):
        t["id"] = i

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accounts": ACCOUNTS,
        "total": len(all_tweets),
        "tweets": all_tweets
    }

    with open("tweets.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(all_tweets)} tweets écrits dans tweets.json")

if __name__ == "__main__":
    main()
