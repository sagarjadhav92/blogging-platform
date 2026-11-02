from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-before-deployment"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blogging_platform.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    posts = db.relationship("Post", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="General")
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comments = db.relationship("Comment", backref="post", cascade="all, delete-orphan", lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user():
    user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    return {"current_user": user}

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = Post.query
    if q:
        query = query.filter(db.or_(Post.title.ilike(f"%{q}%"), Post.content.ilike(f"%{q}%")))
    if category:
        query = query.filter_by(category=category)
    posts = query.order_by(Post.created_at.desc()).all()
    categories = [row[0] for row in db.session.query(Post.category).distinct().order_by(Post.category).all()]
    return render_template("index.html", posts=posts, categories=categories, q=q, selected_category=category)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or len(password) < 6:
            flash("Enter all details. Password must be at least 6 characters.", "error")
        elif User.query.filter(db.or_(User.username == username, User.email == email)).first():
            flash("Username or email already exists.", "error")
        else:
            user = User(username=username, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Account created. Welcome!", "success")
            return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            flash("You are now logged in.", "success")
            return redirect(url_for("index"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("Title and content are required.", "error")
        else:
            post = Post(title=title, category=category, content=content, user_id=session["user_id"])
            db.session.add(post)
            db.session.commit()
            flash("Your blog post has been published.", "success")
            return redirect(url_for("post_detail", post_id=post.id))
    return render_template("post_form.html", post=None)

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = db.get_or_404(Post, post_id)
    return render_template("post_detail.html", post=post)

@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != session["user_id"]:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        if not title or not content:
            flash("Title and content are required.", "error")
        else:
            post.title, post.content, post.category = title, content, category
            db.session.commit()
            flash("Post updated.", "success")
            return redirect(url_for("post_detail", post_id=post.id))
    return render_template("post_form.html", post=post)

@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != session["user_id"]:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("index"))

@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.get_or_404(Post, post_id)
    content = request.form.get("content", "").strip()
    if content:
        db.session.add(Comment(content=content, user_id=session["user_id"], post_id=post.id))
        db.session.commit()
        flash("Comment added.", "success")
    else:
        flash("Comment cannot be empty.", "error")
    return redirect(url_for("post_detail", post_id=post.id))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
