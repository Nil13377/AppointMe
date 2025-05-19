from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from os import path
from datetime import datetime

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
    pfp = db.Column(db.String(200))

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

allowed_extensions = ["jpg", "png", "gif", "jpeg"]

def allowed_img(filename):

    if filename.rsplit(".", 1)[1].lower() in allowed_extensions:
        return filename.rsplit(".", 1)[1].lower()
    
    else:
        return False


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
            if user.pfp:
                session["user_pfp"] = user.pfp
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

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfuly", "success")
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if session.get("user_id"):

        user_id = session.get("user_id")
        business = Business.query.filter_by(user_id=user_id).first()
 
        if request.method == "POST":
            image = request.files.get("profile_picture")

            if image:

                if allowed_img(image.filename):
                    extension = allowed_img(image.filename)
                    new_name = f"user-{user_id}-profilepicture.{extension}"
                    save_path = path.join("static/images", new_name)
                    image.save(save_path)

                    user = User.query.get(user_id)
                    user.pfp = new_name
                    db.session.commit()
                    session["user_pfp"] = user.pfp
                    
                    flash("Image uploaded successfuly", "success")
                    return redirect(url_for("profile"))
                else:
                    flash("Invalid file extension!", "error")
                    return redirect(url_for("profile"))
                
            else:
                flash("Upload an image before submitting!", "error")

        return render_template("profile.html", business=business)
    else:
        flash("Login to view the profile section!", "error")
        return redirect(url_for("login"))
    
@app.route("/create-business", methods=["GET", "POST"])
def create_business():
     
    if session.get("user_id"):

        user_id = session.get("user_id")

        if request.method == "POST":

            business_name = request.form.get("business_name")
            business_description = request.form.get("business_description")
            new_business = Business(user_id=user_id, name=business_name, description=business_description)
            db.session.add(new_business)
            db.session.commit()
            business_id = new_business.id

            services = request.form.getlist("services[]")
            durations = request.form.getlist("durations[]")
            prices = request.form.getlist("prices[]")
            for i in range(len(services)):
                new_service = Services(business_id=business_id, name=services[i], duration=int(durations[i]), price=int(prices[i]))
                db.session.add(new_service)
            db.session.commit()

            flash("Your business and services were added successfuly!", "success")
            return redirect(url_for("profile"))

        return render_template("create_business.html")
    else:
        flash("Login to view the create business section!", "error")
        return redirect(url_for("login"))
    
@app.route("/business-dashboard", methods=["GET", "POST"])
def business_dashboard():
    if not session.get("user_id"):
        flash("Login required!", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    business = Business.query.filter_by(user_id=user_id).first()
    if not business:
        flash("Create a business to view the business dashboard", "error")
        return redirect(url_for("profile"))

    if request.method == "POST":
        date_str = request.form.get("date")
        start_time_str = request.form.get("start_time")
        end_time_str = request.form.get("end_time")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except Exception:
            flash("Invalid date or time format!", "error")
            return redirect(url_for("business_dashboard"))

        new_avail = Availability(
            business_id=business.id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            booked=False
        )
        db.session.add(new_avail)
        db.session.commit()
        flash("Availability added!", "success")
        return redirect(url_for("business_dashboard"))

    return render_template("business_dashboard.html")

@app.route("/get-availability")
def get_availability():
    if not session.get("user_id"):
        return jsonify([])
    user_id = session.get("user_id")
    business = Business.query.filter_by(user_id=user_id).first()
    if not business:
        return jsonify([])
    availabilities = Availability.query.filter_by(business_id=business.id).all()
    events = []
    for avail in availabilities:
        events.append({
            "id": avail.id,
            "title": "Booked" if avail.booked else "Free",
            "start": f"{avail.date}T{avail.start_time}",
            "end": f"{avail.date}T{avail.end_time}",
            "color": "#ff4d4d" if avail.booked else "#4caf50"
        })
    return jsonify(events)


if __name__ == "__main__":
    app.run(debug=True)
