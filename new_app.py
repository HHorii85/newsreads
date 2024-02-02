from flask import Flask, request, jsonify, render_template, send_file, session
import feedparser
from google.cloud import texttospeech
import os
import time
import requests
from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from models import db, User, NewsRead
from flask_migrate import Migrate
import uuid
from datetime import timedelta
from dotenv import load_dotenv
import os



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
# アプリケーションのセッション秘密鍵を設定
app.secret_key = os.getenv('FLASK_APP_SECRET_KEY')

db.init_app(app)
migrate = Migrate(app, db)

load_dotenv()  # .envファイルから環境変数を読み込む

# OpenWeatherMapのAPIキー
OPENWEATHERMAP_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")

# グローバル変数として音声ファイルのリストを定義
audio_files = []

# audioフォルダのパスを作成
audio_folder = os.path.join(app.root_path, 'audio')
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)

# Google Cloudの認証情報を環境変数から取得
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# 初期のニュースフィードのURL
INITIAL_RSS_URL = "https://news.google.com/news/rss/headlines/section/topic/NATION.ja_jp/%E5%9B%BD%E5%86%85?ned=jp&hl=ja&gl=JP"

@app.route('/')
def index():
    user_logged_in = 'user_id' in session
    user_category = None
    if user_logged_in:
        user = User.query.get(session['user_id'])
        user_category = user.last_selected_category if user else None
    
    session['news_session_id'] = str(uuid.uuid4())  #ページ読み込み時にセッションIDをリセット
    return render_template('new_app.html', user_logged_in=user_logged_in, user_category=user_category)

@app.route('/get_news', methods=['POST'])
def get_news():
    data = request.json
    category = data['category']
    client = texttospeech.TextToSpeechClient()
    index = data.get('index', 0)  # クライアントから送信されたインデックス

    # RSSフィードのURLをカテゴリに基づいて選択
    rss_urls = {
        "NATION": "https://news.google.com/news/rss/headlines/section/topic/NATION.ja_jp/%E5%9B%BD%E5%86%85?ned=jp&hl=ja&gl=JP",
        "WORLD": "https://news.google.com/news/rss/headlines/section/topic/WORLD.ja_jp/%E5%9B%BD%E9%9A%9B?ned=jp&hl=ja&gl=JP",
        "BUSINESS": "https://news.google.com/news/rss/headlines/section/topic/BUSINESS.ja_jp/%E3%83%93%E3%82%B8%E3%83%8D%E3%82%B9?ned=jp&hl=ja&gl=JP",
        "POLITICS": "https://news.google.com/news/rss/headlines/section/topic/POLITICS.ja_jp/%E6%94%BF%E6%B2%BB?ned=jp&hl=ja&gl=JP",
        "ENTERTAINMENT": "https://news.google.com/news/rss/headlines/section/topic/ENTERTAINMENT.ja_jp/%E3%82%A8%E3%83%B3%E3%82%BF%E3%83%A1?ned=jp&hl=ja&gl=JP",
        "SPORTS": "https://news.google.com/news/rss/headlines/section/topic/SPORTS.ja_jp/%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%84?ned=jp&hl=ja&gl=JP",
        "SCITECH": "https://news.google.com/news/rss/headlines/section/topic/SCITECH.ja_jp/%E3%83%86%E3%82%AF%E3%83%8E%E3%83%AD%E3%82%B8%E3%83%BC?ned=jp&hl=ja&gl=JP"
    }
    rss_url = rss_urls.get(category)

    if rss_url:
        feed = feedparser.parse(rss_url)
        
        if index < len(feed.entries):
            
            entry = feed.entries[index]  # 最初のニュース項目のみを取得
            
            if 'user_id' in session:
                record_news_reading(session['user_id'], entry.title, entry.link)

            title_with_comma = entry.title.replace(" ", "、")
            synthesis_input = texttospeech.SynthesisInput(text=title_with_comma)
            voice = texttospeech.VoiceSelectionParams(language_code="ja-JP", name="ja-JP-Neural2-B")
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

            # 一時的な音声ファイルを作成
            timestamp = int(time.time())
            audio_file_name = f"temp_{timestamp}.mp3"
            file_path = os.path.join(audio_folder, audio_file_name)  # 完全なパスを作成
            with open(file_path, "wb") as out:
                print("file_path:", file_path)
                out.write(response.audio_content)
                
            # 生成したファイル名をリストに追加し管理
            create_audio_file(response.audio_content, file_path)

            return jsonify({'title': entry.title, 'link': entry.link, 'audio_file': audio_file_name})
        else:
            return jsonify({'error': 'No more news'}), 400
    else:
        return jsonify({'error': 'Invalid category'}), 400
    
def create_audio_file(content, file_name):
    audio_files.append(file_name)
    manage_audio_files()

def manage_audio_files():
    max_files = 20
    while len(audio_files) > max_files:
        file_to_remove = audio_files.pop(0)
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)
    
def record_news_reading(user_id, title, link):
    user = User.query.get(user_id)
    if user:
        username = user.username
        if 'news_session_id' not in session:
            session['news_session_id'] = str(uuid.uuid4())
        session_id = session['news_session_id']
        
        read_news = NewsRead(username=username, title=title, link=link, session_id=session_id)
        db.session.add(read_news)
        db.session.commit()

@app.route('/audio/<filename>')
def audio(filename):
    file_path = os.path.join(audio_folder, filename)  # audioフォルダ内のファイルパス
    try:
        response = send_file(file_path, as_attachment=True)
    finally:
        if os.path.exists(file_path):
            # os.remove(file_path)  # ファイルの削除
            #スルーする
            pass
    return response

def get_japanese_weather_description(weather_main):
    weather_translations = {
        "Clear": "晴れ",
        "Clouds": "曇り",
        "Rain": "雨",
        "Snow": "雪",
        "Drizzle": "霧雨",
        "Thunderstorm": "雷雨"
        # 必要に応じて他の天気状態を追加
    }
    return weather_translations.get(weather_main, weather_main)

@app.route('/get_weather', methods=['GET'])
def get_weather():
    global OPENWEATHERMAP_API_KEY
    
    # クライアントから送信された緯度と経度
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')

    # OpenWeatherMap APIのURL
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ja"
    response = requests.get(url)
    data = response.json()
    
    # one_call_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={latitude}&lon={longitude}&exclude=hourly,minutely&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ja"
    # temp_response = requests.get(one_call_url)
    # temp_data = temp_response.json()
    
    # print(temp_data)

    if response.status_code == 200:
        # 最高気温と最低気温を取得
        # `daily` キーのデータを抽出
        # daily_forecasts = temp_data['daily']  
        # today_forecasts = daily_forecasts[0]  # 今日の天気予報のデータを抽出      
        # max_temp = today_forecasts['temp']['max']
        # min_temp = today_forecasts['temp']['min']
        # 天気の概要と気温を個別に取得
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
       # 天気情報のテキストを作成
        forecast = get_japanese_weather_description(data['weather'][0]['main'])
        weather_text = f"現在の{data['name']}の天気は{data['weather'][0]['description']}で、気温は{data['main']['temp']}度です。今日は一日{forecast}でしょう。"  #今日の最高気温は{max_temp}度で最低気温は{min_temp}度です。
        
        # Text-to-Speech APIで音声に変換
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=weather_text)
        voice = texttospeech.VoiceSelectionParams(language_code="ja-JP", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        tts_response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        # 音声ファイルを保存
        audio_file_name = f"weather_{int(time.time())}.mp3"
        file_path = os.path.join(audio_folder, audio_file_name)
        with open(file_path, "wb") as out:
            out.write(tts_response.audio_content)
            
        # 生成したファイル名をリストに追加し管理
        create_audio_file(tts_response.audio_content, file_path)

        return jsonify({'weather_text': weather_text, 'weather_description': weather_description, 'temperature': temperature,'audio_file': audio_file_name})
    else:
        return jsonify({'error': 'Unable to get weather data'}), 400

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            # ユーザー名が既に存在する場合
            return "Username already exists."

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None #エラーメッセージ用の変数
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        #ユーザ情報をデータベースから取得
        user = User.query.filter_by(username=username).first()
        
        if user is not None and user.check_password(password):
            # パスワードが正しい場合
            session['user_id'] = user.id
            remember_me = request.form.get('remember_me') == 'on'
            if remember_me:
                session.permanent = True
            return redirect(url_for('index'))
        else:
            error = 'ユーザネームまたは、パスワードが間違っています。'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # セッションからユーザーIDを削除
    session.pop('user_id', None)
    # ホームにリダイレクト
    return redirect(url_for('index'))


@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'username': user.username})
        
    return jsonify({'username': None})

@app.route('/update_category', methods=['POST']) 
def update_category():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    category = data.get('category')
    if category:
        user.last_selected_category = category
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Invalid category'}), 400
    
@app.route('/news_list')
def news_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return "ユーザが見つかりません", 404
    
    # ユーザーに関連するニュースをセッションIDごとにグループ化
    news_sessions = db.session.query(NewsRead.session_id, db.func.min(NewsRead.timestamp).label('min_timestamp')).filter_by(username=user.username).group_by(NewsRead.session_id).order_by(db.desc('min_timestamp')).all()
    
    return render_template('news_list.html', news_sessions=news_sessions)

@app.route('/news_list/<session_id>')
def news_session(session_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return "ユーザが見つかりません", 404
    
    news_items = NewsRead.query.filter_by(username=user.username, session_id=session_id).all()
    return render_template('news_session.html', news_items=news_items)

@app.route('/mark_latest_news_as_clicked', methods=['POST'])
def mark_latest_news_as_clicked():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 特定のユーザーの最新のニュース読み上げ記録を検索
    latest_news_read = NewsRead.query.filter_by(username=user.username).order_by(NewsRead.timestamp.desc()).first()

    if latest_news_read:
        latest_news_read.clicked = True
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'No recent news found for user'}), 404

    
if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5000)






# 計画発表振り返り：気になるニュースを後でまとめて振り返るときに，気になったニュースを画面をタップしたらそれを記録しておくなどの簡単に操作できるという工夫が必要．記録したもののみリストアップするとか，，，
# 主な利用はスマートフォンを想定して作ること
# RSSで情報を取得してくるので，本文を取得できているのならそのまま表示したほうが，サイトにアクセスするよりも広告の表示がなかったりしていいと思う．
# ngrokコマンド ngrok http 5000