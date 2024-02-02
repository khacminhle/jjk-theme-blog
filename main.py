import os
from datetime import date
from typing import List
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, user_unauthorized
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, NewUserForm, LoginForm, CommentForm


'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

# Comment Avatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Admin decorator 
def admin_required(func):
    @wraps(func)
    def wrapper_function(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        else:
            return abort(403)
    
    
    return wrapper_function



# TODO: Create a User table for all your registered users. 

class User(db.Model, UserMixin): 
    __tablename__ = 'user_db'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")
 


# CONFIGURE TABLES
    
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = relationship("User", back_populates="posts")
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_db.id"))
    comments: Mapped[List["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
  
    

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Create connection back to user
    author: Mapped[str] = relationship("User", back_populates="comments")
    author_id : Mapped[int] = mapped_column(Integer, ForeignKey("user_db.id"))

    # Create connection backt to post
    post: Mapped[str] = relationship("BlogPost", back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"))



with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["POST", "GET"])
def register(): 
    new_user_form = NewUserForm()
    if new_user_form.validate_on_submit():
        email = new_user_form.email.data
        check_user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if check_user:
            flash("You already have registerred an account with this email. Please sign in.")
            return redirect(url_for('login'))
        else:
            new_user = User(
                name = new_user_form.name.data,
                email = new_user_form.email.data,
                password = generate_password_hash(
                    password=new_user_form.password.data,
                    method="pbkdf2:sha256:600000", 
                    salt_length=8
                    )
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('get_all_posts'))

    return render_template("register.html", form = new_user_form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        check_user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if check_user: 
            if check_password_hash(check_user.password, password):
                login_user(check_user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Incorrect password. Please try again")
                return redirect(url_for('login'))
    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    print(posts)
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text=form.comment.data, 
                author = current_user, 
                post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            print(requested_post.comments)
        else:
            return redirect('/login')
    return render_template("post.html", post=requested_post, form=form)


# TODO: Use a decorator so only an admin user can create a new post

@app.route("/new-post", methods=["GET", "POST"])
@admin_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_required
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    print(post_to_delete)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=False, port=5002)
