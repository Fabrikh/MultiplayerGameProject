from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/api/random')
def generate_random_number():
    random_number = random.randint(2, 6)
    return jsonify({"random_number": random_number})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3999)