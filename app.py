import requests
import json

message = {
    "content": "Hi!, I'm from Google!"
}

# Make a POST request to send the message
url = "http://localhost:5000/api/send"
response = requests.post(url, json=message)

# Retrieve the JSON response
response_data = response.json()

print(response)
