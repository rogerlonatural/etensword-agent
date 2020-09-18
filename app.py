import base64
import json
import os
import threading
import traceback

from flask import Flask, request

from etensword.api.base import process_order

app = Flask(__name__)

processed_commands = {}

lock = threading.Lock()

@app.route('/', methods=['POST'])
def push_message_from_pubsub():
    envelope = request.get_json()
    print(f'Start to process order >>> envelope: {envelope}')
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']
    print(f'pubsub_message: {pubsub_message}')

    try:
        if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
            message_data = base64.b64decode(pubsub_message['data'])
            print(f'message_data: {message_data}')

            payload = json.loads(message_data.decode('utf-8'))
            command_id = payload['command_id']
            if command_id in processed_commands:
                print(f'Duplicated command: {command_id}')
                return '', 204

            processed_commands[command_id] = command_id

            class Message(object):
                pass

            command_message = Message()
            command_message.data = message_data

            with lock:
                process_order(command_message)

    except:
        print('Error on push_message_from_pubsub > %s' % traceback.format_exc().replace('\n',' | '))

    print(f'Message acknowledged {pubsub_message["message_id"]}')
    return '', 204


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
