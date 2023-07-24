from optparse import Values
from unittest import result
import pymysql
import hashlib
import uuid
import os

from flask import Flask, render_template, request, redirect, session, flash
app = Flask(__name__)
app.secret_key = "any-random-string-reshrdjtfkygluvchfjkhlbh"

def encrypt(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_connection():
    
    return pymysql.connect(              
        host="10.0.0.17",
        user="pauhe",
        # host="localhost",
        # user="root",
        password="ALTAR",
        db="pauhe_lost&found",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )


def can_access(id):
    if "logged_in" in session:
        matching_id = session["id"] == int(id)
        is_admin = session["role"] == "admin"

        return matching_id or is_admin
    else:
        return False

def can_accesslost(post_id, session_user_id):
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """
            SELECT userid FROM losts WHERE id = %s
            """
            cursor.execute(sql, (post_id,))
            result = cursor.fetchone()

            if not result:
                return False  # The post doesn't exist

            post_user_id = result["userid"]

    is_admin = session.get("role") == "admin"
    return session_user_id == post_user_id or is_admin




@app.route("/")
def home():
    
    return render_template("home.html")

@app.route("/view")
def view():
    if not can_access(request.args["id"]):
        flash("You don't have permission to do that!")
        return redirect("/")
    
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s"
                values = (
                    request.args["id"]
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
                return render_template("view.html", result=result)
    
@app.route("/user")
def user():
    
    if not "logged_in" in session:
        flash("You are not logged in")
        return redirect("/")    
    if 'admin' in session["role"]:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users"
                cursor.execute(sql)
                result = cursor.fetchall()
                print(result)
        return render_template("user.html", result=result)
    else:
        
        with create_connection() as connection:
                return render_template("view.html",)
    
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                profile = request.files["profile"]
                if not profile:
                    profile_path = "static/images/profile.png"
                else:
                    ext = os.path.splitext(profile.filename)[1]
                    profile_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                    profile.save(profile_path)
                    
                password = request.form["password"]
                encrypted_password = hashlib.sha256(password.encode()).hexdigest()
                print(encrypted_password)

                sql = """INSERT INTO users (first_name, last_name, email, password, profile)
                VALUES (%s, %s, %s, %s, %s)"""
                values = (
                    request.form["first_name"],
                    request.form["last_name"],
                    request.form["email"],
                    encrypted_password,
                    profile_path
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect("/")
    else:
        return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE email = %s AND password = %s"
                values = (
                    request.form["email"],
                    encrypt(request.form["password"])
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session["logged_in"] = True
            session["id"] = result["id"]
            session["first_name"] = result["first_name"]
            session["last_name"] = result["last_name"]
            session["profile"] = result["profile"]
            session["email"] = result["email"]
            session["role"] = result["role"]
            return redirect("/")
        else:
            flash("Wrong username or password!")
            return redirect("/login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/delete")
def delete():
    if not can_access(request.args["id"]):
        flash("You don't have permission to do that!")
        return redirect("/")

    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values)
            connection.commit()
    return redirect("/user")

@app.route("/update", methods=["GET", "POST"])
def update():
    if not can_access(request.args["id"]):
        flash("You don't have permission to do that!")
        return redirect("/")
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                
                profile = request.files["profile"]
                
                
                password = request.form["password"]
                if password: 
                    encrypted_password = hashlib.sha256(password.encode()).hexdigest
                else:
                    encrypted_password = request.form["old_password"]

                if profile: 
                    ext = os.path.splitext(profile.filename)[1]
                    profile_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                    profile.save(profile_path)
                else:
                    profile_path = request.form["old_profile"]

                sql = """UPDATE USERS SET
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    password = %s,
                    profile = %s
                    WHERE id = %s
                """
                values = ( 
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                    profile_path,
                    request.form['id']
                    
                    )
                cursor.execute(sql, values)
                connection.commit()
        return redirect("/")
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s"
                values = (request.args["id"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template("update.html", result=result)

#lost

@app.route("/lost")
def lost():

    if not "logged_in" in session or 'user' in session["role"]:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                SELECT losts.id, losts.image, losts.header, losts.description, users.first_name, users.last_name, users.email
                FROM losts
                INNER JOIN users ON losts.userid = users.id
                """
                cursor.execute(sql)
                lost_results = cursor.fetchall()

            return render_template("lost.html", lost_results=lost_results)

    elif 'admin' in session["role"]:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                SELECT losts.id, losts.image, losts.header, losts.description, users.first_name, users.last_name, users.email
                FROM losts
                INNER JOIN users ON losts.userid = users.id
                """
                cursor.execute(sql)
                lost_results = cursor.fetchall()

            return render_template("posts.html", lost_results=lost_results)
    

@app.route("/deletepost")
def deletepost():
    if not can_accesslost(request.args.get("id"), session.get("id")):
        flash("You don't have permission to do that!")
        return redirect("/")

    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM losts WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values) 
            connection.commit()

    return redirect("/lost")

@app.route("/updatepost", methods=["GET", "POST"])
def updatepost():
    post_id = request.args.get("id")
    session_user_id = session.get("id")

    if not can_accesslost(post_id, session_user_id):
        flash("You don't have permission to do that!")
        return redirect("/")
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                
                image = request.files["image"]

                if image: 
                    ext = os.path.splitext(image.filename)[1]
                    image_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                    image.save(image_path)
                else:
                    image_path = request.form["old_image"]

                sql = """UPDATE LOSTS SET
                    image = %s,
                    header = %s,
                    description = %s
                    WHERE id = %s
                """
                values = ( 
                    image_path,
                    request.form['header'],
                    request.form['description'],
                    request.form['id']
                    
                    )
                cursor.execute(sql, values)
                connection.commit()
        return redirect("/")
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM losts WHERE id = %s"
                values = (request.args["id"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template("updatepost.html", result=result)

@app.route("/viewpost")
def viewpost():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql1 = """
            SELECT losts.id, losts.image, losts.header, losts.description, users.first_name, users.last_name, users.email 
            FROM losts
            INNER JOIN users ON losts.userid = users.id
            WHERE losts.id = %(id)s
            """
            values1 = {
                "id": request.args["id"]
            }
            cursor.execute(sql1, values1)
            lost_result = cursor.fetchone()
            
            return render_template("viewpost.html", lost_result=lost_result)


app.run(debug=True)