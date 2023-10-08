from flask import Flask, request, jsonify, redirect, render_template,make_response, session, url_for
from flask_cors import CORS
import requests
import sys
import json
import re
import sqlite3

app = Flask(__name__)

app.secret_key = "app secret key"

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005"
]

CORS(app, resources={r"/endgame": {"origins": allowed_origins}})

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
        
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO scores (highscore, playedGames, username)
        VALUES (?, ?, ?)
        """
        cursor.execute(insert_query, ("0", "0", username))
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
    
@app.route("/endgame", methods=["POST"])
def endgame():
    try:
        data = request.json
        lastScore = data['score']
        username = data['username']

        conn = sqlite3.connect("userDB.db")
        cursor = conn.cursor()

        scoreQuery = "SELECT * FROM scores WHERE username = ?"
        cursor.execute(scoreQuery, (username,))
        score = cursor.fetchone()

        highscore_value = score[1] 
        played_games_value = score[2] if score else '0'

        played_games_value = str(int(played_games_value) + 1)

        score_as_int = int(lastScore)
        highscore_as_int = int(highscore_value)

        if(score_as_int > highscore_as_int):
            highscore_value = lastScore

        update_query = """
        UPDATE scores
        SET highscore = ?, playedGames = ?
        WHERE username = ?
        """
        cursor.execute(update_query, (highscore_value, played_games_value, username))
          
        conn.commit()
        conn.close()
        response = {'message': 'User added successfully'}
        return jsonify(response), 201 

    except Exception as e:
        response = {"error": str(e)}
        return jsonify(response), 400  # HTTP 400 Bad Request status code

@app.route("/scores", methods=["GET"])
def get_scores():
    conn = sqlite3.connect("userDB.db")
    cursor = conn.cursor()

    query = "SELECT * FROM scores"
    cursor.execute(query)
    scores = cursor.fetchall()

    conn.close()

    return jsonify(scores)

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

    userQuery = "SELECT * FROM users WHERE username = ?"
    cursor.execute(userQuery, (username,))
    user = cursor.fetchone()

    scoreQuery = "SELECT * FROM scores WHERE username = ?"
    cursor.execute(scoreQuery, (username,))
    score = cursor.fetchone()
    highscore_value = score[1] if score else '0'
    played_games_value = score[2] if score else '0'

    conn.close()

    if (user):
        username = username
        resp = make_response(redirect('http://localhost:3000/dashboard'))
        resp.set_cookie('username', username)
        resp.set_cookie('avatar', user[3])
        resp.set_cookie('highscore', highscore_value)
        resp.set_cookie('played_games', played_games_value)
        return resp
        
    else:
        return "You must be logged in to access the dashboard"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
