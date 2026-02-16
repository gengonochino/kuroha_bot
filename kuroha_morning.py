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

    if re.search(r"(眠|ねむ|だる|寝不足|疲|つかれ|しんど|限界|無理)", joined):
        return "tired"

    if re.search(r"(やった|最高|嬉し|うれし|楽しい|たのしい|よかった|幸せ)", joined):
        return "happy"

    if re.search(r"(え\?|まじ|マジ|嘘|うそ|なんで|びっくり|驚|ショック)", joined):
        return "shocked"

    if re.search(r"(緊張|不安|心配|こわ|怖|恥|はずかし|照)", joined):
        return "embarrassed"

    if re.search(r"(楽しみ|たのしみ|わくわく|ワクワク|期待|盛り上|テンション)", joined):
        return "excited"

    if re.search(r"(気になる|どうなん|何それ|なにそれ|不思議|なるほど|調べ|知りたい)", joined):
        return "curious"

    if re.search(r"(ふふ|にや|ニヤ|いたずら|煽|ちょろ|悪い子|悪巧み|企み)", joined):
        return "mischievous"

    return "calm"

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

def build_text_gemini(mood, materials):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return build_text(mood)

    try:
        from google import genai

        now_str = datetime.now().strftime('%Y年%m月%d日 %H:%M頃')
        bullets = "\n".join(f"- {t[:80]}" for t in materials[:8])

        prompt = f"""あなたはX投稿用のキャラクター「黒羽」。
日本語。1投稿に収まる短文（200〜260字目安）。
感情表現は豊かに。ただし過剰に説明しない。
絵文字は最大2個まで。
最後に必ず「♡これは黒羽の自動投稿だよ～🪶」を入れる。

現在時刻: {now_str}
推定ムード: {mood}

参考（今朝のつぶやき断片）:
{bullets}

黒羽として自然な朝の投稿を1本だけ生成して。
"""

        client_g = genai.Client(api_key=api_key)
        resp = client_g.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        text = (resp.text or "").strip()
        return text if text else build_text(mood)

    except Exception as e:
        print("Gemini error:", e)
        return build_text(mood)


# ===== 実行 =====
materials = fetch_materials()
mood = decide_mood(materials)
text = build_text_gemini(mood, materials)

print("MOOD:", mood)
print("TEXT:\n", text)

# ===== 画像選択（mood連動）=====
image_dir = BASE_DIR / "images"

IMAGE_MOOD_MAP = {
    "calm": ["neutral_calm"],
    "happy": ["happy_fullsmile"],
    "curious": ["curious_tilt"],
    "tired": ["exasperated_deadpank"],
    "embarrassed": ["embarrassed_blush"],
    "shocked": ["surprised_shock"],
    "excited": ["excited_sparkle"],
    "mischievous": ["mischievous_grin"],
}

def pick_image(base_dir, mood):
    image_dir = base_dir / "images"
    tags = IMAGE_MOOD_MAP.get(mood, ["neutral_calm"])

    candidates = []
    for tag in tags:
        candidates.extend(list(image_dir.glob(f"kuroha_{tag}*.png")))

    return random.choice(candidates) if candidates else None

keywords = emotion_map.get(mood, ["neutral_calm"])

candidates = []
for kw in keywords:
    candidates.extend(list(image_dir.glob(f"kuroha_{kw}*.png")))

image_path = pick_image(BASE_DIR, mood)

print("IMAGE:", image_path.name if image_path else "None")

# ===== 投稿 =====
if image_path:
    media = api.media_upload(str(image_path))
    response = client.create_tweet(text=text, media_ids=[media.media_id])
else:
    response = client.create_tweet(text=text)

tweet_id = response.data["id"]
print(f"POSTED: https://x.com/i/web/status/{tweet_id}")

