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

@app.route("/")
def home():
    
    return render_template("home.html")

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
    """
    elif session["role"] == "user":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s"
                values = (
                    request.args["id"]
                    )
                cursor.execute(sql, values)
                result = cursor.fetchall()
        return render_template("user.html", result=result)
"""

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

def can_access(id):
    if "logged_in" in session:
        matching_id = session["id"] == int(id)
        is_admin = session["role"] == "admin"

        return matching_id or is_admin
    else:
        return False


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
    


app.run(debug=True)