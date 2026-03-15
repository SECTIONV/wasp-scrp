"""
OSINT X Scraper — GitHub Actions
Utilise twscrape (authentification compte X)
"""

import asyncio
import json
import os
import sys
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

MAX_TWEETS_PER_ACCOUNT = 10
HOURS_LOOKBACK = 24

# ─────────────────────────────────────────
# CREDENTIALS DU COMPTE X SECONDAIRE
# Stockés dans les GitHub Secrets :
#   X_USERNAME  → votre pseudo X
#   X_PASSWORD  → votre mot de passe
#   X_EMAIL     → votre email X
# ─────────────────────────────────────────
X_USERNAME = os.environ.get("X_USERNAME", "")
X_PASSWORD = os.environ.get("X_PASSWORD", "")
X_EMAIL    = os.environ.get("X_EMAIL", "")


async def main():
    if not ACCOUNTS:
        print("ERREUR : Aucun compte dans ACCOUNTS")
        sys.exit(1)

    if not X_USERNAME or not X_PASSWORD or not X_EMAIL:
        print("ERREUR : Variables X_USERNAME / X_PASSWORD / X_EMAIL manquantes")
        sys.exit(1)

    from twscrape import API, gather
    from twscrape.logger import set_log_level
    set_log_level("ERROR")

    api = API()
    await api.pool.add_account(X_USERNAME, X_PASSWORD, X_EMAIL, X_PASSWORD)
    await api.pool.login_all()

    since_dt = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    all_tweets = []
    seen_ids = set()

    for username in ACCOUNTS:
        print(f"Scraping @{username}...")
        try:
            user = await api.user_by_login(username)
            if not user:
                print(f"  Compte @{username} introuvable")
                continue

            count = 0
            async for tweet in api.user_tweets(user.id, limit=MAX_TWEETS_PER_ACCOUNT * 3):
                if tweet.id in seen_ids:
                    continue
                tweet_dt = tweet.date
                if tweet_dt.tzinfo is None:
                    tweet_dt = tweet_dt.replace(tzinfo=timezone.utc)
                if tweet_dt < since_dt:
                    break

                media_url = ""
                if tweet.media and tweet.media.photos:
                    media_url = tweet.media.photos[0].url

                all_tweets.append({
                    "id": count,
                    "src": "X",
                    "acc": "@" + username,
                    "time": tweet_dt.strftime("%H:%M"),
                    "date_in": tweet_dt.strftime("%Y-%m-%d"),
                    "url": f"https://x.com/{username}/status/{tweet.id}",
                    "mediaUrl": media_url,
                    "raw": tweet.rawContent or tweet.content or "",
                    "selected": False,
                    "llm_done": False,
                    "status": "pending",
                    "desc": "",
                    "fields": {
                        "ctrl": "", "date": "", "pays": "", "reg": "", "ville": "",
                        "lat": "", "lon": "", "acteur": "", "type": "", "media": "", "conf": {}
                    }
                })
                seen_ids.add(tweet.id)
                count += 1
                if count >= MAX_TWEETS_PER_ACCOUNT:
                    break

            print(f"  → {count} tweet(s)")

        except Exception as e:
            print(f"  Erreur @{username} : {e}")

    # Trier par date décroissante
    all_tweets.sort(key=lambda x: x["date_in"] + x["time"], reverse=True)
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
    asyncio.run(main())
