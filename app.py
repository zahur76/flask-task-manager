import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        print(existing_user)
        # same as if existing_user["username"] == request.form.get("username")
        if existing_user:
            flash("Username already exist!")
            return redirect(url_for("register"))
        # else, if username does not exist
        # get fields from registration form
        else:
            register = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            # insert into mongodb
            mongo.db.users.insert_one(register)

            # put username into session cookie
            session["user"] = request.form.get("username").lower()
            flash("Registration Successful!")

            # redirect to user profile page username required
            return redirect(url_for('profile', username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        # existing_user is a dictionary for that user
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        # if exising_user returns a dictionary
        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                # redirect to user profile page username required
                return redirect(url_for('profile', username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get session username from db using cookie dictionary
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    return render_template("profile.html", username=username)


@app.route("/logout")
def logout():
    flash("You have been logged out!")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        new_task = {"category_name": request.form.get("category_name"),
                    "task_name": request.form.get("task_name"),
                    "task_description": request.form.get("task_description"),
                    "is_urgent": request.form.get("is_urgent"),
                    "due_date": request.form.get("due_date"),
                    "created_by": session["user"]}
        mongo.db.tasks.insert_one(new_task)
        flash("Tasks successfully added")
        return redirect(url_for("get_tasks"))
    categories = mongo.db.catogories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
