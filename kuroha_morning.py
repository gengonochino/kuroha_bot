# -*- coding: utf-8 -*-

import os
import random
import re
from pathlib import Path
from datetime import datetime
import tweepy
from dotenv import load_dotenv

# ベースディレクトリ
BASE_DIR = Path(__file__).resolve().parent

# .env が存在する場合のみ読み込む（GitHub Actionsでは存在しない）
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))

# 環境変数の取得
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# Tweepy認証
auth = tweepy.OAuth1UserHandler(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET
)

api = tweepy.API(auth)
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# ===== 朝トレンド取得 =====
def fetch_materials():
    resp = client.search_recent_tweets(
        query="おはよう lang:ja -is:retweet -is:reply",
        max_results=10,
        user_auth=True
    )
    texts = []
    if resp and resp.data:
        for t in resp.data:
            texts.append(t.text)
    return texts

def decide_mood(texts):
    joined = " ".join(texts)

    if re.search("眠|ねむ|だる|つら|しんど", joined):
        return "sleepy"
    if re.search("仕事|学校|バイト|会議", joined):
        return "serious"
    if re.search("寒|暑|雨|雪", joined):
        return "season"
    return "normal"

def build_text(mood):
    now_str = datetime.now().strftime('%Y年%m月%d日 %H:%M頃')

    if mood == "sleepy":
        body = "まだ眠い人、多そうだね…は〜。\nゆっくりでいいよ、今日も生きてるだけでえらい。"
    elif mood == "serious":
        body = "今日も忙しくなりそうだね。\n無理しすぎないでいこう。"
    elif mood == "season":
        body = "ちょっと季節に振り回されがちな朝だね。\n体調気をつけていこう。"
    else:
        body = "みんなそれぞれの朝だね。\n今日も少しずつ進んでいこう。"

    return f"""{now_str}、おはよう🪶
{body}
♡これは黒羽の自動投稿だよ～🪶"""

# ===== 実行 =====
materials = fetch_materials()
mood = decide_mood(materials)
text = build_text(mood)

print("MOOD:", mood)
print("TEXT:\n", text)

# ===== 画像選択（mood連動）=====
image_dir = BASE_DIR / "images"

emotion_map = {
    "sleepy": ["neutral_calm", "embarrassed_blush"],
    "serious": ["exasperated_deadpank"],
    "season": ["surprised_shock", "curious_tilt"],
    "normal": ["happy_fullsmile", "excited_sparkle", "mischievous_grin"],
}

keywords = emotion_map.get(mood, ["neutral_calm"])

candidates = []
for kw in keywords:
    candidates.extend(list(image_dir.glob(f"kuroha_{kw}*.png")))

image_path = random.choice(candidates) if candidates else None

print("IMAGE:", image_path.name if image_path else "None")

# ===== 投稿 =====
if image_path:
    media = api_v1.media_upload(str(image_path))
    response = client.create_tweet(text=text, media_ids=[media.media_id])
else:
    response = client.create_tweet(text=text)

tweet_id = response.data["id"]
print(f"POSTED: https://x.com/i/web/status/{tweet_id}")

