from flask import Flask, jsonify
import secrets

app = Flask(__name__)

@app.route('/api/random')
def generate_random_number():
    secret_random_number = secrets.randbelow(6) + 1
    return jsonify({"random_number": secret_random_number})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3999)