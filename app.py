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
# Used to connect to mongodb
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# Used for session cookie
app.secret_key = os.environ.get("SECRET_KEY")
# creating mongodb using ["MONGO_URI"]
mongo = PyMongo(app)


@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    # Obtain all tasks in db. Use fo loop in html
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.tasks.find({"$text": {"$search": query}}))
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # will return the full record as a dictionary if it exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        # check if username already exists in db
        # if exisiting user returns an Object
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
        # if exising_user returns a dictionary and not null
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
    # clear cookie from session
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        # if there is a request.form.get("is_urgent") then:
        if request.form.get("is_urgent"):
            is_urgent = "on"
        else:
            is_urgent = "off"
        new_task = {"category_name": request.form.get("category_name"),
                    "task_name": request.form.get("task_name"),
                    "task_description": request.form.get("task_description"),
                    "is_urgent": is_urgent,
                    "due_date": request.form.get("due_date"),
                    "created_by": session["user"]}
        # Create new task in mongodb tasks collection
        mongo.db.tasks.insert_one(new_task)
        flash("Tasks successfully added")
        return redirect(url_for("get_tasks"))
    # Provide category field in rendered page for form
    categories = mongo.db.catogories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
# task_id obtained from task.html page
def edit_task(task_id):
    if request.method == "POST":
        # if there is a request.form.get("is_urgent") then:
        if request.form.get("is_urgent"):
            is_urgent = "on"
        else:
            is_urgent = "off"
        new_task = {"category_name": request.form.get("category_name"),
                    "task_name": request.form.get("task_name"),
                    "task_description": request.form.get("task_description"),
                    "is_urgent": is_urgent,
                    "due_date": request.form.get("due_date"),
                    "created_by": session["user"]}
        # Create new task in mongodb tasks collection
        mongo.db.tasks.update_one(
            {"_id": ObjectId(task_id)}, {"$set": new_task})
        flash("Tasks successfully Updated")
        return redirect(url_for("get_tasks"))

    # obtain db using task_id from task.html page
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    categories = mongo.db.catogories.find().sort("category_name", 1)
    return render_template("edit_task.html", task=task, categories=categories)


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    # remove Object with specific Id
    mongo.db.tasks.remove({"_id": ObjectId(task_id)})
    flash("Task has been removed!")
    return redirect(url_for("get_tasks"))


@app.route("/categories")
def categories():
    # Will still work without list function
    # Will obtain all Objects in category. Must use for loop in html
    categories = list(mongo.db.catogories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        # Insert into mongodb category database
        mongo.db.catogories.insert_one(
            {"category_name": request.form.get("category_name")})
        flash("New Category added")
        return redirect(url_for("categories"))

    categories = mongo.db.catogories.find()
    return render_template("add_category.html", categories=categories)


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        category = {"category_name": request.form.get("category_name")}
        mongo.db.catogories.update_one(
            {"_id": ObjectId(category_id)}, {"$set": category})
        flash("Category name updated!")
        return redirect(url_for("categories"))
    # We only need 1 category in edit page since editing only 1 object
    category = mongo.db.catogories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.catogories.remove({"_id": ObjectId(category_id)})
    flash("Category has been deleted")
    return redirect(url_for('categories'))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
