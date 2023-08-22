from flask import Flask, request, jsonify, redirect, render_template
import requests
import sys
import json
import re
import sqlite3

app = Flask(__name__)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@app.route("/", methods=["GET"])
def default():
    try:
        return render_template("registration.html")
    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code


@app.route("/users", methods=["POST"])
def add_user():
    try:
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check if passwords match
        if password != confirm_password:
            raise ValueError("Passwords do not match")

        avatar_file = request.files["avatar"]

        conn = sqlite3.connect("userDB.db")
        cursor = conn.cursor()

        # prettier-ignore
        insert_query = """
        INSERT INTO users (username, password, avatar)
        VALUES (?, ?, ?)
        """

        cursor.execute(insert_query, (username, password, avatar_file))
        conn.commit()
        conn.close()

        response = {"message": "User added successfully"}
        return jsonify(response), 201  # HTTP 201 Created status code
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
