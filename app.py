import base64
import os
import traceback

from flask import Flask, request

from etensword.api.base import process_order

app = Flask(__name__)


# def test():
#     print('pull_commands_from_pubsub')
#     stime = time.time() * 1000
#     pull_message_from_pubsub()
#     while True:
#         time.sleep(0.1)
#         if time.time() * 1000 - stime > 5000:
#             return


@app.route('/', methods=['POST'])
def push_message_from_pubsub():
    envelope = request.get_json()
    print(f'envelope: {envelope}')
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

            class Message(object):
                pass

            command_message = Message()
            command_message.data = message_data
            process_order(command_message)
    except:
        print('Error on push_message_from_pubsub > %s' % traceback.format_exc())

    return ('', 204)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
