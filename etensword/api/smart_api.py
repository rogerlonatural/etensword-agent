import subprocess as sp
import time
import traceback

from etensword.api.base import OrderAgentBase, logger

ORDER_PRICE_MARKET = 'MKT'  # 市價單則任意值即可
ORDER_REST_OF_DAY = 'ROD'  # ROD當日有效
ORDER_IMMEDIATE_OR_CANCEL = 'IOC'  # IOC立即成交否則不成交
ORDER_FILL_OR_KILL = 'FOK'  # FOK全部成交否則不成交
ORDER_NON_DAY_TRADING = '1'  # 非當沖
ORDER_DAY_TRADING = '0'  # 當沖
ORDER_TYPE_BUY = 'B'
ORDER_TYPE_SELL = 'S'
ORDER_PRICE_LIMIT = 'LMT'  # 委託價格

EXPECTED_OPEN_INTEREST_ANY = 'Any'
EXPECTED_OPEN_INTEREST_BUY = 'B'
EXPECTED_OPEN_INTEREST_SELL = 'S'
EXPECTED_OPEN_INTEREST_EMPTY = 'Empty'


class OrderAgent(OrderAgentBase):

    def args_to_api_info(self, args):
        api_info = ' '.join(args)
        return api_info.replace(self.config.get('smart_api', 'exec_path'), '')

    def _exec_command(self, args):
        try:
            command_output = sp.run(args, capture_output=True, check=True)
            if command_output.returncode == 0:
                result = command_output.stdout.decode('big5').strip('\r\n')
                if '請開啟Smart API' in result:
                    return False, result
                else:
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
            if try_time > 3:
                success = False
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

    # expected = ( Any | B | S | Empty )
    def _has_open_interest(self, expected=EXPECTED_OPEN_INTEREST_ANY):
        logger.info('_has_open_interest >> expected: %s' % (expected,))
        api = 'OnOpenInterest.exe'
        on_open_interest_path = self.config.get('smart_api', 'exec_path') + api
        args = [on_open_interest_path]
        retry = 0
        while True:
            success, result = self._exec_command(args)
            if not success:
                break
            result = result.strip()

            if expected == EXPECTED_OPEN_INTEREST_BUY and ',B,' in result:
                break

            if expected == EXPECTED_OPEN_INTEREST_SELL and ',S,' in result:
                break

            if expected == EXPECTED_OPEN_INTEREST_EMPTY and len(result) == 0:
                break

            if expected == EXPECTED_OPEN_INTEREST_ANY and (',S,' in result or ',B,' in result or len(result) == 0):
                break

            if '請開啟Smart API' in result:
                success = False
                break
            if retry > 10:
                result += '... Failed after retry %s times' % retry
                success = False
                break
            retry += 1
            time.sleep(0.5 * retry)
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
        responses.append(self._has_open_interest())
        if not responses[-1]['success']:
            return responses
        responses.append(self._mayday())

        if not responses[-1]['success']:
            return responses
        responses.append(self._change_product(product))
        responses.append(self._has_open_interest(EXPECTED_OPEN_INTEREST_EMPTY))

        return responses

    def CloseAndSell(self, product, price):
        responses = []
        responses.append(self._change_product(product))
        if not responses[-1]['success']:
            return responses

        responses.append(self._has_open_interest())
        if not responses[-1]['success']:
            return responses

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

        order_number = responses[-1]['result']
        responses.append(self._get_account(order_number))

        if not responses[-1]['success']:
            return responses
        responses.append(self._change_product(product))
        responses.append(self._has_open_interest(EXPECTED_OPEN_INTEREST_SELL))

        return responses

    def CloseAndBuy(self, product, price):
        responses = []
        responses.append(self._change_product(product))
        if not responses[-1]['success']:
            return responses

        responses.append(self._has_open_interest())
        if not responses[-1]['success']:
            return responses

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

        order_number = responses[-1]['result']
        responses.append(self._get_account(order_number))

        if not responses[-1]['success']:
            return responses
        responses.append(self._change_product(product))
        responses.append(self._has_open_interest(EXPECTED_OPEN_INTEREST_BUY))

        return responses
