from flask import Flask, jsonify, request

app = Flask(__name__)

class MailBuffer():
    
    def __init__(self,size):
        self.buffer = {}
        self.length = 0
        self.size = size
    
    def addNewMessage(self,source,destination, message):
        
        if self.buffer.get(destination):           
            self.buffer[destination].append((source,message))
                  
        else:
            self.buffer[destination] = [(source,message)]
            
        self.length += 1
        
        return {"sent":True}
            
    def getNewMessage(self,destination):
        
        source, m = (None,None)
        
        if self.buffer.get(destination):

            source, m = self.buffer[destination].pop(0)
            
            self.length -= 1
            
            if len(self.buffer[destination]) == 0:
                self.buffer.pop(destination)
        
        return {"source":source, "content":m} 
    
    def __repr__(self):
        
        return f"Buffer Content:\n{self.buffer}"
            
            
mailBuffer = MailBuffer(size = 20)


@app.route('/api/send', methods=['POST'])
def send_message():
    # Get message from sender

    message = request.json

    source = message["source"]
    destination = message["destination"]
    m = message["content"]

    result = mailBuffer.addNewMessage(source,destination,m)
    
    print(mailBuffer)  

    return jsonify(result)

@app.route('/api/deliver', methods=['GET'])
def deliver_message():
    # Deliver a message on request

    destination = request.args.get('id')

    response = mailBuffer.getNewMessage(destination)

    print(mailBuffer)
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
