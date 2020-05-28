import json
import os
import socket
import subprocess as sp
import sys
import time
import traceback
from google.cloud import pubsub_v1

from etensword import get_config
from etensword.agent_commands import AgentCommand
from etensword.agent_logging import get_logger
from etensword.utils import publish_message_to_pubsub

logger = get_logger('EtenSwordAgent')

ORDER_TYPE_BUY = 'B'
ORDER_TYPE_SELL = 'S'
ORDER_PRICE_LIMIT = 'LMT'  # 委託價格
ORDER_PRICE_MARKET = 'MKT'  # 市價單則任意值即可
ORDER_REST_OF_DAY = 'ROD'  # ROD當日有效
ORDER_IMMEDIATE_OR_CANCEL = 'IOC'  # IOC立即成交否則不成交
ORDER_FILL_OR_KILL = 'FOK'  # FOK全部成交否則不成交
ORDER_NON_DAY_TRADING = '1'  # 非當沖
ORDER_DAY_TRADING = '0'  # 當沖


def add_result(results, result):
    results.append(result)
    return results


class OrderAgent(object):

    def __init__(self, config=None):
        if not config:
            config = get_config()
        self.config = config

    def is_agent_active(self):
        hostname = socket.gethostname()
        if os.path.exists(hostname):
            with open(hostname, 'r') as f:
                status = f.readline()
                return status == 'Active'
        else:
            return True

    def SetAgentActive(self, status):
        responses = []
        api = 'set_agent_active'
        try:
            hostname = socket.gethostname()
            s = 'Active' if status else 'Inactive'
            with open(hostname, 'w') as f:
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
        try:
            command = payload['command']
            props = payload['props'] if 'props' in payload else {}
            expire_at = payload['expire_at'] if 'expire_at' in payload else payload['publish_time'] + AgentCommand.COMMAND_TIMEOUT
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
            return False, msg

    def args_to_api_info(self, args):
        api_info = ' '.join(args)
        return api_info.replace(self.config.get('smart_api', 'exec_path'), '')


    def _exec_command(self, args):
        try:
            command_output = sp.run(args, capture_output=True, check=True)
            if command_output.returncode == 0:
                result = command_output.stdout.decode('big5').strip('\r\n')
                logger.info('Success to run command: %s , result: %s' % (args, result))
                return True, result
            else:
                error_str = command_output.stderr.decode('big5').strip('\r\n')
                logger.error('Failed to execute command: %s. Reason: %s' % (args, error_str))
                return False, 'Error: %s' % error_str
        except:
            error_str = 'Failed to execute command: %s. Reason: %s' % (args, traceback.format_exc())
            logger.error(error_str)
            return False, error_str

    # 使用Order.exe 執行檔，需要帶入的參數如下
    # 商品：期權交易商品，例如2018年第四個月份的大台指期TXFD8。
    # 買賣：B買、S賣
    # 價格：委託價格，市價單則任意值即可
    # 量：1至100，100為期交所上限
    # 價格類別：LMT限價單、MKT市價單
    # 委託類別：ROD當日有效、IOC立即成交否則不成交、FOK全部成交否則不成交
    # 是否當沖：1非當沖、0當沖
    def _put_order(self, product, order_type, price=0, qty=1, trade_type=ORDER_REST_OF_DAY):
        api = 'Order.exe'
        order_exec_path = self.config.get('smart_api', 'exec_path') + api
        price_type = ORDER_PRICE_MARKET if price == 0 else ORDER_PRICE_LIMIT
        trade_type = ORDER_IMMEDIATE_OR_CANCEL if price_type == ORDER_PRICE_MARKET else ORDER_REST_OF_DAY
        args = [order_exec_path,
                product,
                order_type,
                str(price),
                str(qty),
                price_type,
                trade_type,
                ORDER_NON_DAY_TRADING]
        success, result = self._exec_command(args)
        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def _delete_order(self, order_number):
        api = 'Order.exe'
        order_exec_path = self.config.get('smart_api', 'exec_path') + api
        args = [order_exec_path, 'Delete', order_number]
        success, result = self._exec_command(args)
        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def _change_product(self, product):
        api = 'ChangeProdid.exe'
        change_prodid_exec_path = self.config.get('smart_api', 'exec_path') + api
        args = [change_prodid_exec_path, product]
        success, result = self._exec_command(args)
        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def _get_account(self, order_number='ALL', timeout=3):
        api = 'GetAccount.exe'
        get_account_exec_path = self.config.get('smart_api', 'exec_path') + api
        args = [get_account_exec_path, order_number]
        stime = time.time()
        try_time = 1
        while True:
            success, result = self._exec_command(args)
            if not success:
                break
            if '全部成交' in result:
                break
            if '委託失敗' in result:
                success = False
                break
            if 'Nodata' in result:
                success = False
                if timeout == 0:
                    break
                elif time.time() - stime > timeout * 60:
                    result += '... after %s minutes' % str(timeout)
                    break
            time.sleep(try_time)
            try_time += 1

        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def _mayday(self):
        api = 'MayDay.exe'
        mayday_exec_path = self.config.get('smart_api', 'exec_path') + api
        args = [mayday_exec_path]
        success, result = self._exec_command(args)
        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def _is_order_finished(self):
        api = 'GetUnfinished.exe'
        get_unfinished_path = self.config.get('smart_api', 'exec_path') + api
        args = [get_unfinished_path]
        success, result = self._exec_command(args)
        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def _has_open_interest(self):
        api = 'OnOpenInterest.exe'
        on_open_interest_path = self.config.get('smart_api', 'exec_path') + api
        args = [on_open_interest_path]
        success, result = self._exec_command(args)
        return dict(
            api=self.args_to_api_info(args),
            success=success,
            result=result
        )

    def HasOpenInterest(self, product):
        responses = []
        responses.append(self._change_product(product))
        if not responses[-1]['success']:
            return responses

        responses.append(self._has_open_interest())
        return responses

    def MayDay(self, product):
        responses = []
        responses.append(self._change_product(product))
        if not responses[-1]['success']:
            return responses
        responses.append(self._mayday())
        return responses

    def CloseAndSell(self, product, price):
        responses = []
        responses.append(self._change_product(product))
        if not responses[-1]['success']:
            return responses

        retry = 0
        while True:
            responses.append(self._has_open_interest())
            if not responses[-1]['success']:
                return responses
            if ',S,' in responses[-1]['result'] or ',B,' in responses[-1]['result']:
                break
            if retry > 3:
                return  responses
            retry += 1

        # close first, verify the open interest is BUY
        if len(responses[-1]['result']) > 0:
            if ',B,' in responses[-1]['result']:
                responses.append(self._put_order(product, ORDER_TYPE_SELL, price))
                if not responses[-1]['success']:
                    return responses
                # check order accepted
                order_number = responses[-1]['result']
                responses.append(self._get_account(order_number))
                if not responses[-1]['success']:
                    return responses
            elif ',S,' in responses[-1]['result']:
                return responses

        # then sell
        responses.append(self._put_order(product, ORDER_TYPE_SELL, price))
        if not responses[-1]['success']:
            return responses

        # check order accepted
        order_number = responses[-1]['result']
        responses.append(self._get_account(order_number))

        return responses

    def CloseAndBuy(self, product, price):
        responses = []
        responses.append(self._change_product(product))
        if not responses[-1]['success']:
            return responses

        retry = 0
        while True:
            responses.append(self._has_open_interest())
            if not responses[-1]['success']:
                return responses
            if ',S,' in responses[-1]['result'] or ',B,' in responses[-1]['result']:
                break
            if retry > 3:
                return  responses
            retry += 1

        # close first, verify the open interest is SELL
        if len(responses[-1]['result']) > 0:
            if ',S,' in responses[-1]['result']:
                responses.append(self._put_order(product, ORDER_TYPE_BUY, price))
                if not responses[-1]['success']:
                    return responses
                # check order accepted
                order_number = responses[-1]['result']
                responses.append(self._get_account(order_number))
                if not responses[-1]['success']:
                    return responses
            elif ',B,' in responses[-1]['result']:
                return responses

        # then sell
        responses.append(self._put_order(product, ORDER_TYPE_BUY, price))
        if not responses[-1]['success']:
            return responses

        # check order accepted
        order_number = responses[-1]['result']
        responses.append(self._get_account(order_number))

        return responses


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


#  {'product': 'TXFE0', 'close_price': 10715, 'signal': 'SHORT', 'match_time': '2020-05-05 19:40:00'}
def process_order(message):
    config = get_config()
    message_data = message.data.decode('utf-8')
    logger.info("Received message: {}".format(message_data))

    payload = json.loads(message_data)
    agent = payload['agent'] if 'agent' in payload else ''
    command_id = payload['command_id']
    if agent and agent != config.get('order_agent', 'agent_id'):
        logger.info('Skip command: %s of other agent' % command_id)
        message.ack()
        return

    agent = OrderAgent()
    responses = agent.run(payload)
    command = payload['command']
    try:
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
    message.ack()
    logger.info('Message acknowledged. command_id: %s' % command_id)


def feedback_execution_result(command, command_id, result):
    config = get_config()
    logger.info('command result: %s' % result)
    project_id = config.get('gcp', 'PROJECT_ID')
    topic = config.get('gcp', 'TOPIC_FEEDBACK')
    msg_object = {
        'command': command,
        'message': {
            'execution_result': json.dumps(result)
        },
        'agent': config.get('order_agent', 'agent_id'),
        'command_id': command_id
    }
    publish_message_to_pubsub(project_id, topic, msg_object)


def main(argv):
    while True:
        pull_message_from_pubsub()
        time.sleep(0.25)


if __name__ == '__main__':
    stime = time.time()

    main(sys.argv[1:])

    logger.info("done, elapsed time > %s" % (time.time() - stime))

