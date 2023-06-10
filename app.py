import requests
import json

message = {
    "source":"Adam",
    "destination":"Bob",
    "content":"ciaociao va?"
}

# Make a POST request to send the message
url = "http://localhost:5000/api/send"
response = requests.post(url, json=message)

# Retrieve the JSON response
response_data = response.json()

print(response)
print(response_data)
