import json
import requests
import socket
import time
from google.cloud import pubsub_v1

from etensword.agent_logging import get_logger

logger = get_logger(__name__)


def publish_message_to_pubsub(project_id, topic, msg_object):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic)
    msg_object['hostname'] = socket.gethostname()
    msg_object['publish_time'] = time.time()

    def callback(message_future):
        # When timeout is unspecified, the exception method waits indefinitely.
        if message_future.exception(timeout=30):
            logger.error('Publishing message on {} threw an Exception {}.'.format(
                topic, message_future.exception()))
        else:
            logger.info('Message sent OK, result: %s, command: %s' % (message_future.result(), msg_object))

    message_future = publisher.publish(topic_path, data=json.dumps(msg_object).encode("UTF-8"))
    message_future.add_done_callback(callback)
    return message_future
