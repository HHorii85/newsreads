import feedparser
import os
from google.cloud import texttospeech
import pygame

# Google Cloudの認証情報を設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "rational-logic-388613-c086065380ae.json"

# Text-to-Speechクライアントの初期化
client = texttospeech.TextToSpeechClient()

# pygameの初期化
pygame.mixer.init()

# RSSフィードのURL
# rss_url = "https://news.google.com/news/rss/headlines/section/topic/NATION.ja_jp/%E5%9B%BD%E5%86%85?ned=jp&hl=ja&gl=JP"

# カテゴリと対応するRSSフィードのURL
categories = {
    "国内ニュース": "https://news.google.com/news/rss/headlines/section/topic/NATION.ja_jp/%E5%9B%BD%E5%86%85?ned=jp&hl=ja&gl=JP",
    "国際ニュース": "https://news.google.com/news/rss/headlines/section/topic/WORLD.ja_jp/%E5%9B%BD%E9%9A%9B?ned=jp&hl=ja&gl=JP",
    "ビジネス関連": "https://news.google.com/news/rss/headlines/section/topic/BUSINESS.ja_jp/%E3%83%93%E3%82%B8%E3%83%8D%E3%82%B9?ned=jp&hl=ja&gl=JP",
    "政治関連": "https://news.google.com/news/rss/headlines/section/topic/POLITICS.ja_jp/%E6%94%BF%E6%B2%BB?ned=jp&hl=ja&gl=JP",
    "エンタメ関連": "https://news.google.com/news/rss/headlines/section/topic/ENTERTAINMENT.ja_jp/%E3%82%A8%E3%83%B3%E3%82%BF%E3%83%A1?ned=jp&hl=ja&gl=JP",
    "スポーツ関連": "https://news.google.com/news/rss/headlines/section/topic/SPORTS.ja_jp/%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%84?ned=jp&hl=ja&gl=JP",
    "テクノロジー関連": "https://news.google.com/news/rss/headlines/section/topic/SCITECH.ja_jp/%E3%83%86%E3%82%AF%E3%83%8E%E3%83%AD%E3%82%B8%E3%83%BC?ned=jp&hl=ja&gl=JP"
}

# カテゴリを表示し、ユーザーに選択させる
print("以下のカテゴリから選択してください：")
for category in categories.keys():
    print(category)

selected_category = input("カテゴリを入力してください：")

# # 選択されたカテゴリのURLを取得
rss_url = categories.get(selected_category)

if rss_url:
    # フィードを取得
    feed = feedparser.parse(rss_url)

    # 各記事のタイトルとリンクを表示し、タイトルを読み上げる
    for entry in feed.entries:
        print(f"タイトル: {entry.title}")
        print(f"リンク: {entry.link}\n")

        # 全角空白を「、」に置換
        entry.title = entry.title.replace(" ", "、")

        # 音声合成のリクエスト設定
        synthesis_input = texttospeech.SynthesisInput(text=entry.title)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name="ja-JP-Neural2-B",  # これは一例です。利用可能なNeural2音声名に変更してください
            # ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # テキストを音声に変換
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        # 一時的な音声ファイルを作成
        with open("temp.mp3", "wb") as out:
            out.write(response.audio_content)

        # 音声ファイルを再生
        pygame.mixer.music.load("temp.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # 再生が終了するまで待機
            pygame.time.Clock().tick(10)
else:
    print("無効なカテゴリです。")
    
# 一時ファイルを削除
os.remove("temp.mp3")
