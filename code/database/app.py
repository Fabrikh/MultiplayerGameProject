from flask import Flask, request, jsonify, redirect, render_template,make_response, session, url_for
import requests
import sys
import json
import re
import sqlite3

app = Flask(__name__)

app.secret_key = "app secret key"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

@app.route("/register", methods=["POST"])
def register():
    try:
        username = request.form.get("username")
        password = request.form.get("password")
        avatarId = request.form.get("avatarId")
        confirm_password = password

        # Check if passwords match
        if password != confirm_password:
            raise ValueError("Passwords do not match")

        conn = sqlite3.connect("userDB.db")
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if (user):
            resp = make_response(redirect('http://localhost:3000/register'))
            resp.set_cookie('error_already_registered', "True")
            return resp


        # prettier-ignore
        insert_query = """
        INSERT INTO users (username, password, avatar)
        VALUES (?, ?, ?)
        """

        cursor.execute(insert_query, (username, password, avatarId))
        conn.commit()
        conn.close()

        resp = make_response(redirect('http://localhost:3005/'))
        resp.set_cookie('error_wrong_credentials', "False")
        resp.set_cookie('error_already_registered', "False")
        return resp
    
    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code


@app.route("/login", methods=["POST"])
def login():
    try:
        provided_username = request.form.get("username")
        provided_password = request.form.get("password")

        conn = sqlite3.connect("userDB.db")
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        cursor.execute(query, (provided_username, provided_password))
        user = cursor.fetchone()

        conn.close()

        if user is not None:
            username = provided_username
            resp = make_response(redirect('http://localhost:3005/'))
            resp.set_cookie('username', username)
            resp.set_cookie('avatar', user[3])
            resp.set_cookie('error_wrong_credentials', "False")
            return resp
        else:
            resp = make_response(redirect('http://localhost:3005/'))
            resp.set_cookie('error_wrong_credentials', "True")
            return resp

    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code

@app.route("/users", methods=["GET"])
def get_all_users():
    conn = sqlite3.connect("userDB.db")
    cursor = conn.cursor()

    query = "SELECT * FROM users"
    cursor.execute(query)
    users = cursor.fetchall()

    conn.close()

    return jsonify(users)


@app.route("/dashboard", methods=["GET"])
def user_dashboard():
    username = request.cookies.get('username')  

    conn = sqlite3.connect("userDB.db")
    cursor = conn.cursor()

    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    conn.close()

    if (user):
        username = username
        resp = make_response(redirect('http://localhost:3000/dashboard'))
        resp.set_cookie('username', username)
        resp.set_cookie('avatar', user[3])
        return resp
        
    else:
        return "You must be logged in to access the dashboard"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
