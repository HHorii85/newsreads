# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
from datetime import datetime

db = SQLAlchemy()

def jst_now():
    utc_now = datetime.utcnow()
    jst_zone = pytz.timezone('Asia/Tokyo')
    jst_now = utc_now.replace(tzinfo=pytz.utc).astimezone(jst_zone)
    return jst_now

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    last_selected_category = db.Column(db.String(50), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class NewsRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    link = db.Column(db.String(200), nullable=False)
    session_id = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=jst_now)
    clicked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ReadNews {self.username} {self.title}>"