import json
import os
import time
import traceback
from importlib import import_module

import requests
from google.cloud import pubsub_v1

from etensword import get_config
from etensword.agent_commands import AgentCommand
from etensword.agent_logging import get_logger

BUILD_NUM = '20.0904.00'
logger = get_logger('EtenSwordAgent-' + BUILD_NUM)


class OrderAgentFactory:

    @staticmethod
    def get_order_agent(order_agent_type='smart_api'):
        try:
            order_agent_module = import_module('etensword.api.%s' % order_agent_type, 'OrderAgent')
            order_agent_class = getattr(order_agent_module, 'OrderAgent')
            return order_agent_class()

        except Exception as e:
            print('Failed to get order agent %s, retry again' % order_agent_type)
            print(traceback.format_exc())
            return None


class OrderAgentBase(object):

    def __init__(self, config=None):
        if not config:
            config = get_config()
        self.config = config

    def is_agent_active(self):
        agent_id = self.config.get('order_agent', 'agent_id')
        if os.path.exists(agent_id):
            with open(agent_id, 'r') as f:
                status = f.readline()
                return status == 'Active'
        else:
            return True

    def SetAgentActive(self, status):
        responses = []
        api = 'set_agent_active'
        try:
            agent_id = self.config.get('order_agent', 'agent_id')
            s = 'Active' if status else 'Inactive'
            with open(agent_id, 'w') as f:
                f.write(s)
            response = dict(
                api=api,
                success=True,
                result='Agent is now %s' % s
            )
        except:
            err_str = 'Failed to set agent status. Error: %s' % traceback.format_exc()
            print(err_str)
            response = dict(
                api=api,
                success=False,
                result=err_str
            )
        responses.append(response)
        return responses

    def run(self, payload):
        command = payload['command']
        try:
            props = payload['props'] if 'props' in payload else {}
            expire_at = payload['expire_at'] if 'expire_at' in payload else payload[
                                                                                'publish_time'] + AgentCommand.COMMAND_TIMEOUT
            if time.time() > expire_at:
                return [dict(
                    api=command,
                    success=False,
                    result='Command is not executed because it is expired (Timeout=%s sec)' % AgentCommand.COMMAND_TIMEOUT
                )]
            if command != AgentCommand.ENABLE_AGENT and not self.is_agent_active():
                return [dict(
                    api=command,
                    success=False,
                    result='Command is not executed because agent is inactive'
                )]
            if command == AgentCommand.CHECK_AGENT:
                return [dict(
                    api=command,
                    success=True,
                    result='I am great!'
                )]
            if command == AgentCommand.DISABLE_AGENT:
                return self.SetAgentActive(False)

            if command == AgentCommand.ENABLE_AGENT:
                return self.SetAgentActive(True)

            if command == AgentCommand.CHECK_OPEN_INTEREST:
                return self.HasOpenInterest(props['product'])

            if command == AgentCommand.MAYDAY:
                return self.MayDay(props['product'])

            if command == AgentCommand.CLOSE_AND_SELL:
                return self.CloseAndSell(props['product'], props['price'])

            if command == AgentCommand.CLOSE_AND_BUY:
                return self.CloseAndBuy(props['product'], props['price'])

        except:
            msg = 'Failed to execute command. Error: %s' % traceback.format_exc()
            logger.error(msg)
            return [dict(
                api=command,
                success=False,
                result=msg
            )]

    def HasOpenInterest(self, product):
        raise NotImplementedError()

    def MayDay(self, product):
        raise NotImplementedError()

    def CloseAndSell(self, product, price):
        raise NotImplementedError()

    def CloseAndBuy(self, product, price):
        raise NotImplementedError()


def pull_message_from_pubsub():
    config = get_config()
    project_id = config.get('gcp', 'PROJECT_ID')
    subscription_name = config.get('gcp', 'SUBSCRIPTION')
    subscriber = pubsub_v1.SubscriberClient()
    # The `subscription_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/subscriptions/{subscription_name}`
    subscription_path = subscriber.subscription_path(
        project_id, subscription_name
    )

    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=process_order
    )
    logger.info('Order agent type: %s' % config.get('order_agent', 'order_agent_type'))
    logger.info("Listening for messages on {}..".format(subscription_path))
    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result()

        except KeyboardInterrupt as e:
            streaming_pull_future.cancel()
            raise e
        except Exception as e:  # noqa
            logger.error('Failed to process message. Error: %s' % traceback.format_exc())
            streaming_pull_future.cancel()


def process_order(message):
    responses = None
    command = None
    command_id = ''
    try:
        config = get_config()
        message_data = message.data.decode('utf-8')
        logger.info("Received message: {}".format(message_data))

        payload = json.loads(message_data)
        agent = payload['agent'] if 'agent' in payload else ''
        command_id = payload['command_id']
        if agent and agent != config.get('order_agent', 'agent_id'):
            logger.info('Skip command: %s of other agent' % command_id)
            try:
                message.ack()
            except AttributeError:
                pass
            return

        print('Execute command: %s' % payload)
        command = payload['command']
        retry = 0
        while True:
            agent = OrderAgentFactory.get_order_agent(order_agent_type=config.get('order_agent', 'order_agent_type'))
            if agent:
                break
            if retry > 3:
                raise Exception('Failed to get order agent after 3 retry')
            retry += 1
            time.sleep(retry)

        responses = agent.run(payload)
        print('Publish feedback: %s' % responses)

        feedback_execution_result(command, command_id, {
            'success': responses[-1]['success'],
            'results': responses
        })

    except:
        logger.error('Failed to parse responses, command: %s, responses: %s', (command, responses))
        logger.error(traceback.format_exc())
        feedback_execution_result(command, command_id, {
            'success': False,
            'results': responses
        })
    try:
        message.ack()
    except AttributeError:
        pass
    logger.info('Message acknowledged. command_id: %s' % command_id)


def send_agent_feedback(payload):
    url = 'https://asia-east2-etensword.cloudfunctions.net/api_send_agent_feedback'
    retry = 0
    while True:
        response = requests.post(url, data=json.dumps(payload))
        if response.status_code == 204:
            print('Feedback sent OK')
            return
        if retry > 3:
            print('Failed to feedback after retry')
            return
        retry += 1
        time.sleep(retry)


def feedback_execution_result(command, command_id, result):
    config = get_config()
    logger.info('command result: %s' % result)
    # project_id = config.get('gcp', 'PROJECT_ID')
    # topic = config.get('gcp', 'TOPIC_FEEDBACK')
    msg_object = {
        'command': command,
        'message': {
            'execution_result': json.dumps(result)
        },
        'agent': config.get('order_agent', 'agent_id'),
        'command_id': command_id
    }
    send_agent_feedback(msg_object)
    # publish_message_to_pubsub(project_id, topic, msg_object)


def start(args):
    while True:
        pull_message_from_pubsub()
        time.sleep(0.1)
