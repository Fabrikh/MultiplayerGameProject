from flask import Flask, jsonify, request

app = Flask(__name__)
  
# Ciclo col timeout        

@app.route('/api/heartbeatrequest', methods=['POST'])
def send_message():
    # Get message from sender

    message = request.json

    source = message["source"]
    destination = message["destination"]
    m = message["content"]

    result = mailBuffer.addNewMessage(source,destination,m)


    return jsonify(result)

@app.route('/api/heartbeatreply', methods=['GET'])
def deliver_message():
    # Deliver a message on request

    destination = request.args.get('id')

    response = mailBuffer.getNewMessage(destination)
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
