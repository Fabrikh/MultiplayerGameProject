from flask import Flask, request, jsonify, redirect, render_template, session, url_for
import requests
import sys
import json
import re
import sqlite3
import base64

app = Flask(__name__)

app.secret_key = "app secret key"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@app.route("/register", methods=["GET"])
def register_page():
    try:
        return render_template("registration.html")
    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code


@app.route("/register", methods=["POST"])
def register():
    try:
        username = request.form.get("username")
        password = request.form.get("password")
        avatar_base64_image = request.form.get("base64Image")
        confirm_password = password

        # Check if passwords match
        if password != confirm_password:
            raise ValueError("Passwords do not match")

        conn = sqlite3.connect("userDB.db")
        cursor = conn.cursor()

        # prettier-ignore
        insert_query = """
        INSERT INTO users (username, password, avatar)
        VALUES (?, ?, ?)
        """

        cursor.execute(insert_query, (username, password, avatar_base64_image))
        conn.commit()
        conn.close()

        response = {"message": "User added successfully"}
        return jsonify(response), 201  # HTTP 201 Created status code
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
            # Store user data in the session
            session["username"] = provided_username
            return redirect(url_for("user_dashboard", username=provided_username))
        else:
            response = {
                "success": False,
                "message": "Login failed",
            }
            return jsonify(response)

    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code


@app.route("/login", methods=["GET"])
def login_page():
    try:
        return render_template("login.html")
    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code


@app.route("/", methods=["GET"])
def default():
    try:
        return redirect(url_for("login"))
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


@app.route("/dashboard")
def user_dashboard():
    username = request.args.get("username")

    conn = sqlite3.connect("userDB.db")
    cursor = conn.cursor()

    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    avatar = cursor.fetchone()

    conn.close()

    if "username" in session:
        return render_template("dashboard.html", username=username, avatar=avatar[3])
    else:
        return "You must be logged in to access the dashboard"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
