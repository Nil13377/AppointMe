from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "77F92BD4AEE93FFBAEDFC3F15D848"


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///appointme.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(100), nullable = False, unique = True)
    password = db.Column(db.String(200), nullable = False)
    name = db.Column(db.String(100), nullable = False)
    surname = db.Column(db.String(100), nullable = False)

class Business(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(100), nullable = False)
    description = db.Column(db.String(200))

class Services(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    business_id = db.Column(db.Integer, db.ForeignKey("business.id"))
    name = db.Column(db.String(100), nullable = False)
    duration = db.Column(db.Integer)
    price = db.Column(db.Integer, nullable = False)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    business_id = db.Column(db.Integer, db.ForeignKey("business.id"))
    date = db.Column(db.Date, nullable = False)
    start_time = db.Column(db.Time, nullable = False)
    end_time = db.Column(db.Time, nullable = False)
    booked = db.Column(db.Boolean, nullable = False)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.session.query(User).filter_by(email = email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_name"] = user.name
            session["user_surname"] = user.surname
            return redirect(url_for("profile"))
        else:
            flash("Email or password are incorect! Try again", "error")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        password = request.form.get("password")
        if db.session.query(User).filter_by(email = email).first():
            flash("Email already exists! Use a diffrent email or login", "error")
            return redirect(url_for("register"))
        else:
            hashed = generate_password_hash(password)
            new_user = User(name = name, surname = surname, email = email, password = hashed)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration complete! You can login now", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
