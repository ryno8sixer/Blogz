from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:root@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'somerandomstring'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(800))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login','signup','index','blog']
    if request.endpoint in allowed_routes:
        pass
    else:
        if 'username' not in session:
            return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            flash('Logged In', 'success')
            return redirect('/newpost')
        else:
            flash('User or password incorrect or user does not exist.', 'error')
    return render_template('login.html')   

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ver_password = request.form['verify']
        name_error=''
        pass_error=''

        if username=='':
            name_error='Please insert a username.'
        elif len(username)<3 or len(username)>20:
            name_error='Username must be between 3-20 characters.'
        elif ' ' in username:
            name_error='Username may not contain spaces.'

        if password=='':
            pass_error='Please insert a password.'
        elif len(password)<3 or len(password)>10:
            pass_error='Password must be between 3-10 characters.'
        elif ' ' in password:
            pass_error='Password may not contain spaces.'
        elif ver_password != password:
            pass_error='Passwords do not match.'

        if name_error=='' and pass_error=='':
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                username = username.title()
                new_user = User(username,password)
                db.session.add(new_user)
                db.session.commit()
                flash("{} user created".format(username), "success")
                session['username'] = username
                return redirect('/newpost')
            else:
                flash("Username is taken please choose another one", "error")
        else:
            return render_template('signup.html', username=username, name_error=name_error, pass_error=pass_error) 
    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')    

@app.route('/')
def index():
    users = User.query.order_by(User.username.asc()).all()
    return render_template('index.html', users=users)

@app.route('/blog')
def blog():
    if "id" in request.args:
        id = request.args.get("id")
        title = Blog.query.filter_by(id=id).first().title
        body = Blog.query.filter_by(id=id).first().body
        owner = Blog.query.filter_by(id=id).first().owner
        return render_template("singleblog.html", title=title, body=body, owner=owner)

    if "username" in request.args:
        username = request.args.get("username")
        owner = User.query.filter_by(username=username).first()
        blogs = Blog.query.filter_by(owner=owner).order_by(Blog.id.desc()).all()
        return render_template("singleuser.html", username=username, owner=owner, blogs=blogs)
    else:
        blogs = Blog.query.order_by(Blog.id.desc()).all()
        return render_template('blog.html', blogs=blogs)

@app.route('/newpost', methods=['GET', 'POST'])
def add_blog():
    if request.method=='GET':
        return render_template('newpost.html')

    if request.method=='POST':
        title=request.form['title']
        body=request.form['body']
        owner=User.query.filter_by(username=session['username']).first()
        blog_error=''
    if title=='' or body=='':
        blog_error='Title and/or Body field may not be left empty.'
    if blog_error=='':
        new_blog=Blog(title,body,owner)
        db.session.add(new_blog)
        db.session.commit()
        query_url= './blog?id='+ str(new_blog.id)
        return redirect(query_url)
    else:
        return render_template('newpost.html', error=blog_error, title=title, body=body)

if __name__=='__main__':
    app.run()