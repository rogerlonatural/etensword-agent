import os
import time

from flask import Flask

from etensword.api.base import pull_message_from_pubsub

app = Flask(__name__)

@app.route('/')
def pull_commands_from_pubsub():
    print('pull_commands_from_pubsub')
    stime = time.time() * 1000
    while True:
        pull_message_from_pubsub()
        if time.time() * 1000 - stime > 59000:
            return
        time.sleep(0.1)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))