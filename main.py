from flask import Flask, render_template
from config import *
from pusher_api import *

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

@app.route('/')
def example():
    # Initalize by passing through the authentication details
    Pusher = PusherAPI(app_id = PUSHER["app_id"], key = PUSHER["key"], secret = PUSHER["secret"], cluster = PUSHER["cluster"])
    # Data to send via websocket
    Pusher.load({"data":{"message":"hello_world!"},"name":"my-event","channels":"my-test-channel"})
    # HTTP code & Response from the API is returned  
    Response = Pusher.execute()
    return render_template('html/index.html', pusher_key=PUSHER["key"],  pusher_cluster=PUSHER["cluster"])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)