import os
import click
from flask import Flask, render_template
from flask import request, url_for, flash
from flask import redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required, current_user, logout_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'swcfsfy_xylxydt'
db = SQLAlchemy(app)

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))
    actor =db.Column(db.String(60))


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=False, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')

    name='kuxue'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988', 'actor': 'akk'},
        {'title': 'Dead Poets Society', 'year': '1989', 'actor': 'yzn'},
        {'title': 'A Perfect World', 'year': '1993', 'actor': 'was'},
        {'title': 'Leon', 'year': '1994', 'actor': 'akk'},
        {'title': 'Mahjong', 'year': '1996', 'actor': 'was'},
        {'title': 'Swallowtail Butterfly', 'year': '1996', 'actor':'hnm'},
        {'title': 'King of Comedy', 'year': '1999', 'actor':'ert'},
        {'title': 'Devils on the Doorstep', 'year': '1999','actor':'def'},
        {'title': 'WALL-E', 'year': '2008','actor':'ret'},
        {'title': 'The Pork of Music', 'year': '2012','actor':'thy'},
    ]
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'],actor=m['actor'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done.')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        user = User.query.first()    # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)         # 登入用户
            current_user.name = username
            db.session.commit()
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页
        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面
    return render_template('login.html')


@app.route('/logout')
@login_required  # 用于视图保护
def logout():
    logout_user()  # 登出用户
    current_user.name = 'Admin'
    db.session.commit()
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页


@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def handle_sort_option(sort_option):
    if sort_option == 'year_asc':
        return Movie.query.order_by(Movie.year.asc()).all()
    elif sort_option == 'year_desc':
        return Movie.query.order_by(Movie.year.desc()).all()
    else:
        # Default sorting (ascending by year)
        return Movie.query.order_by(Movie.year.asc()).all()

def handle_movie_submission():
    title = request.form.get('title')
    year = request.form.get('year')
    actor = request.form.get('actor')

    if not title or not year or not actor or len(year) > 4 or len(title) > 60 or len(actor) > 60:
        flash('无效的输入。')
    else:
        movie = Movie(title=title, year=year, actor=actor)
        db.session.add(movie)
        db.session.commit()
        flash('电影已创建。')

@app.route('/', methods=['GET', 'POST'])
def index():
    sort_option = request.form.get('sort_option')
    if request.method == 'POST' and sort_option:
        # Handle sorting logic
        movies = handle_sort_option(sort_option)
    else:
        movies = Movie.query.all()
        if request.method == 'POST' and current_user.is_authenticated:
            # Handle movie submission
            handle_movie_submission()

    user = User.query.first()
    return render_template('index.html', user=user, movies=movies, sort_option=sort_option)



@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']
        actor = request.form['actor']
        if not title or not year or not actor or len(year) > 4 or len(title) > 60 or len(actor) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))
        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        movie.actor = actor
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页
    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    return render_template('settings.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        movies_by_title = Movie.query.filter(Movie.title.like(f'%{search_term}%')).all()
        movies_by_actor = Movie.query.filter(Movie.actor.like(f'%{search_term}%')).all()
        return render_template('search_results.html', movies_by_title=movies_by_title, movies_by_actor=movies_by_actor, search_term=search_term)
    return render_template('search.html')
