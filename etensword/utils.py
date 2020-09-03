import datetime
import decimal
import json
import socket
import time

from google.cloud import pubsub_v1

from etensword.agent_logging import get_logger

logger = get_logger(__name__)

def my_json_converter(o):
    if isinstance(o, decimal.Decimal):
        return str(o)
    if isinstance(o, datetime):
        return o.strftime('%Y-%m-%d %H:%M:%S')


def publish_message_to_pubsub(project_id, topic, msg_object):
    # Configure the batch to publish as soon as there is ten messages,
    # one kilobyte of data, or one second has passed.
    batch_settings = pubsub_v1.types.BatchSettings(
        max_messages=10,  # default 100
        max_bytes=1024,  # default 1 MB
        max_latency=1,  # default 10 ms
    )

    # Configure the retry settings. Defaults will be overwritten.
    retry_settings = {
        "interfaces": {
            "google.pubsub.v1.Publisher": {
                "retry_codes": {
                    "publish": [
                        "ABORTED",
                        "CANCELLED",
                        "DEADLINE_EXCEEDED",
                        "INTERNAL",
                        "RESOURCE_EXHAUSTED",
                        "UNAVAILABLE",
                        "UNKNOWN",
                    ]
                },
                "retry_params": {
                    "messaging": {
                        "initial_retry_delay_millis": 100,  # default: 100
                        "retry_delay_multiplier": 1.3,  # default: 1.3
                        "max_retry_delay_millis": 600000,  # default: 60000
                        "initial_rpc_timeout_millis": 5000,  # default: 25000
                        "rpc_timeout_multiplier": 1.0,  # default: 1.0
                        "max_rpc_timeout_millis": 600000,  # default: 30000
                        "total_timeout_millis": 600000,  # default: 600000
                    }
                },
                "methods": {
                    "Publish": {
                        "retry_codes_name": "publish",
                        "retry_params_name": "messaging",
                    }
                },
            }
        }
    }

    publisher = pubsub_v1.PublisherClient(client_config=retry_settings, batch_settings=batch_settings)
    topic_path = publisher.topic_path(project_id, topic)
    msg_object['hostname'] = socket.gethostname()
    msg_object['publish_time'] = time.time()

    def callback(message_future):
        # When timeout is unspecified, the exception method waits indefinitely.
        if message_future.exception(timeout=120):
            logger.error('Publishing message on {} threw an Exception {}.'.format(
                topic, message_future.exception()))
        else:
            logger.info('Message sent OK, result: %s, command: %s' % (message_future.result(), msg_object))

    message_future = publisher.publish(topic_path, data=json.dumps(msg_object, default=my_json_converter).encode("UTF-8"))
    message_future.add_done_callback(callback)
    return message_future
