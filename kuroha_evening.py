# -*- coding: utf-8 -*-
import tweepy
from dotenv import load_dotenv
import os
import random
import glob
from datetime import datetime, timedelta
import traceback

load_dotenv()

# v2 Client
client = tweepy.Client(
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    access_token=os.getenv("ACCESS_TOKEN"),
    access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"),
    bearer_token=os.getenv("BEARER_TOKEN")
)

# v1.1 API for media upload
auth = tweepy.OAuth1UserHandler(
    os.getenv("CONSUMER_KEY"),
    os.getenv("CONSUMER_SECRET"),
    os.getenv("ACCESS_TOKEN"),
    os.getenv("ACCESS_TOKEN_SECRET")
)
api = tweepy.API(auth)

my_id = 1641676619386593280

now = datetime.now()
date_str = now.strftime("%Y年%m月%d日 %H:%M頃")

# 過去24時間のstart_time修正（ミリ秒なしで厳密フォーマット）
start_time = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

tweets = client.get_users_tweets(id=my_id, start_time=start_time, tweet_fields=["public_metrics"])

best_tweet = None
max_imp = 0
best_link = ""
if tweets.data:
    for tweet in tweets.data:
        imp = tweet.public_metrics['impression_count']
        if imp > max_imp:
            max_imp = imp
            best_tweet = tweet
            best_link = f"https://x.com/aiartchino/status/{tweet.id}"

summary = f"今日一番見てもらえた投稿はこれ！（{max_imp}インプレッション）\n{best_link}" if best_tweet else "今日はまだ投稿少ないね…明日もよろしくね"

text = f"{date_str}、おやすみ🪶\n{summary}\n♡これは黒羽の自動投稿だよ～🪶"

# 夜は穏やかムード
images = glob.glob("images/*content*.png") + glob.glob("images/*neutral*.png") + glob.glob("images/*sleepy*.png")
image_path = random.choice(images) if images else "/Users/daisukenakagome/kuroha_bot/images/kuroha_neutral_calm.png"

print(text)
print(f"画像: {os.path.basename(image_path)}")

try:
    media = api.media_upload(filename=image_path)
    response = client.create_tweet(text=text, media_ids=[media.media_id])
    print("夜投稿成功！")
except Exception as e:
    traceback.print_exc()
