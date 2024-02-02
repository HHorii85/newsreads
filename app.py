# app.py
from flask import Flask, request, redirect, url_for, render_template
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db.init_app(app)

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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # ユーザー認証のロジック...
        # 成功した場合、new_app.htmlへリダイレクト
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/')
def index():
    return "Home Page"

if __name__ == '__main__':
    app.run(debug=True)
