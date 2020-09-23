import json
import time
import traceback
from importlib import import_module

import requests
from google.cloud import pubsub_v1

from etensword import get_config
from etensword.agent_commands import AgentCommand
from etensword.agent_logging import get_logger

BUILD_NUM = '20.0923.01'
logger = get_logger('EtenSwordAgent-' + BUILD_NUM)

class OrderAgentFactory:

    @staticmethod
    def get_order_agent(order_agent_type='smart_api'):
        retry = 0
        while True:
            try:
                order_agent_module = import_module('etensword.api.%s' % order_agent_type, 'OrderAgent')
                order_agent_class = getattr(order_agent_module, 'OrderAgent')
                order_agent = order_agent_class()
                return order_agent

            except Exception as e:
                print('Failed to get order agent %s, retry again' % order_agent_type)
                print(traceback.format_exc().replace('\n', '>>'))
                retry += 1
                if retry > 3:
                    print('Failed to get order agent %s after retry' % order_agent_type)
                    return
                time.sleep(retry)


class OrderAgentBase(object):

    def __init__(self, config=None):
        if not config:
            config = get_config()
        self.config = config
        self.trace_id = None
        self.agent_id = None
        self.account_id = None
        self.trace_id = None

    def run(self, payload):
        command = payload['command']
        self.trace_id = payload['command_id']
        self.agent_id = payload['agent']
        try:
            props = payload['props'] if 'props' in payload else {}
            expire_at = payload['expire_at'] if 'expire_at' in payload else payload[
                                                                                'publish_time'] + AgentCommand.COMMAND_TIMEOUT
            if time.time() > expire_at and command != AgentCommand.CHECK_OPEN_INTEREST:
                return [dict(
                    api=command,
                    success=False,
                    result='Command is not executed because it is expired (Timeout=%s sec)' % AgentCommand.COMMAND_TIMEOUT
                )]

            if command == AgentCommand.CHECK_AGENT:
                return [dict(
                    api=command,
                    success=True,
                    result='I am great!'
                )]

            # Real agent related commands below
            self.InitAgent(self.agent_id)

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
            logger.error('[%s] %s' % (self.trace_id, msg))
            return [dict(
                api=command,
                success=False,
                result=msg
            )]
        finally:
            self.CloseAgent()

    def HasOpenInterest(self, product):
        raise NotImplementedError()

    def MayDay(self, product):
        raise NotImplementedError()

    def CloseAndSell(self, product, price):
        raise NotImplementedError()

    def CloseAndBuy(self, product, price):
        raise NotImplementedError()

    def InitAgent(self, agent_id):
        pass

    def CloseAgent(self):
        pass


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


processed_commands = {}

def process_order(message):
    responses = None
    command = None
    command_id = ''
    agent_id = ''
    try:
        config = get_config()
        message_data = message.data.decode('utf-8')
        logger.info("Received message: {}".format(message_data))

        payload = json.loads(message_data)
        agent_id = payload['agent'] if 'agent' in payload else ''
        command_id = payload['command_id']
        command = payload['command']
        print('[%s] Execute command: %s' % (command_id, payload))

        is_other_agent = False
        if config.has_section('agent_account_mapping'):
            agent_ids = config.options('agent_account_mapping')
            if agent_id and agent_id not in agent_ids:
                is_other_agent = True

        elif agent_id != config.get('order_agent', 'agent_id'):
            is_other_agent = True

        if is_other_agent:
            logger.info('[%s] Skip command of other agent' % command_id)
            try:
                message.ack()
                print('[%s] Message acknowledged.' % command_id)
            except AttributeError:
                pass
            return

        if command_id not in processed_commands:
            processed_commands[command_id] = command_id
        else:
            logger.info(f'Skip duplicated command: {command_id}')
            try:
                message.ack()
                print('[%s] Message acknowledged.' % command_id)
            except AttributeError:
                pass
            return

        order_agent = OrderAgentFactory.get_order_agent(order_agent_type=config.get('order_agent', 'order_agent_type'))
        responses = order_agent.run(payload)

        print('[%s] Publish feedback: %s' % (command_id, responses))
        feedback_execution_result(agent_id, command, command_id, {
            'success': responses[-1]['success'],
            'results': responses
        })

    except:
        print('[%s] Failed to parse responses, command: %s, responses: %s' % (command_id, command, responses))
        print('[%s] %s' % (command_id, traceback.format_exc().replace('\n', '>>')))
        feedback_execution_result(agent_id, command, command_id, {
            'success': False,
            'results': responses
        })

    try:
        message.ack()
    except AttributeError:
        pass
    print('[%s] Message acknowledged.' % command_id)


def send_agent_feedback(payload, command_id=''):
    url = 'https://asia-east2-etensword.cloudfunctions.net/api_send_agent_feedback'
    retry = 0
    status_code = None
    response_text = None
    while True:
        try:
            response = requests.post(url, data=json.dumps(payload))
            status_code = response.status_code
            response_text = response.text
            if status_code == 204:
                print('[%s] Feedback sent OK' % command_id)
                return
        except:
            print('[%s] Failed to send feedback, retry, %s' % (command_id, traceback.format_exc().replace('\n', '>>')))

        if retry > 3:
            print('[%s] Failed to feedback after retry %s %s' % (command_id, status_code, response_text))
            return
        retry += 1
        time.sleep(retry)

def feedback_execution_result(agent, command, command_id, result):
    try:
        logger.info('[%s] Feedback command result: %s' % (command_id, result))
        # project_id = config.get('gcp', 'PROJECT_ID')
        # topic = config.get('gcp', 'TOPIC_FEEDBACK')
        msg_object = {
            'command': command,
            'message': {
                'execution_result': json.dumps(result)
            },
            'agent': agent,
            'command_id': command_id
        }
        send_agent_feedback(msg_object, command_id)
    except:
        logger.info('[%s] Failed to feedback execution result, ignored' % command_id)
        pass
    # publish_message_to_pubsub(project_id, topic, msg_object)

def start(args):
    while True:
        pull_message_from_pubsub()
        time.sleep(0.1)
