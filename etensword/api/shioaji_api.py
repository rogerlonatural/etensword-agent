import json
import time
import traceback

import shioaji as sj
from shioaji.constant import Action, Status

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


class OrderAgent(OrderAgentBase):

    def __init__(self):
        super().__init__()

        self.api = sj.Shioaji(backend='http', simulation=False)
        self.person_id = self.config.get('shioaj_api', 'person_id')
        self.passwd = self.config.get('shioaj_api', 'passwd')
        self.account_id = self.config.get('shioaj_api', 'account_id')
        self.ca_passwd = self.config.get('shioaj_api', 'ca_passwd')
        self.ca_path = self.config.get('shioaj_api', 'ca_path')

        self._do_login()

        logger.info('CA path: %s' % self.config.get('shioaj_api', 'ca_path'))
        self.api.activate_ca(
            ca_path=self.ca_path,
            ca_passwd=self.ca_passwd,
            person_id=self.person_id
        )


    def _do_login(self):
        retry = 0
        while True:
            try:
                self.api.login(
                    self.person_id,
                    self.passwd
                )
                all_accounts = self.api.list_accounts()
                logger.info('login and list accounts >>> %s' % all_accounts)
                for fa in all_accounts:
                    if fa.account_id == self.account_id:
                        self.account = fa
                        logger.info('Login with account_id: %s' % self.account.account_id)
                        break

                if not self.account:
                    raise Exception('No account for account_id: %s' % self.account_id)

                logger.info('Set default account: %s' % self.account)
                self.api.set_default_account(self.account)

                return dict(
                    api='login',
                    success=True,
                    result='Login with account_id: %s' % self.account_id
                )

            except Exception as e:
                if retry > 3:
                    print('Login failed after retry. %s' % traceback.format_exc())
                    return dict(
                        api='login',
                        success=False,
                        result=str(e)
                    )
                retry += 1
                time.sleep(retry * 2)
                print('_do_login start retry %s' % retry)

    def _wrap_get_account_openposition_data(self, results):
        wrap_results = [dict(
            product=result['Code'],
            action=Action.Sell if result['OrderBS'] == 'S' else Action.Buy,
            qty=int(float(result['Volume'])),
            price=int(float(result['ContractAverPrice'])),
            real_price=int(float(result['RealPrice']))
        ) for result in results if len(result) > 0]
        return json.dumps(wrap_results)

    def _has_open_interest(self):
        retry = 0
        while True:
            try:
                if not self.account:
                    self._do_login()

                positions = self.api.get_account_openposition(product_type="0", query_type="0", account=self.account)
                print('_has_open_interest > get_account_openposition > data: %s' % positions.data())

                return dict(
                    api='get_account_openposition',
                    success=True,
                    result=self._wrap_get_account_openposition_data(positions.data())
                )
            except Exception as e:
                if retry > 3:
                    print(traceback.format_exc())
                    return dict(
                        api='get_account_openposition',
                        success=False,
                        result=str(e)
                    )
                time.sleep(retry)
                retry += 1
                print('_has_open_interest start retry %s' % retry)

    def _check_order_info(self, product, expected, timeout=60):
        print('_check_order_info > product: %s, expected: %s' % (product, expected))
        stime = time.time()
        retry = 0
        while True:
            response = self._has_open_interest()
            print('_check_order_info > _has_open_interest > %s' % response)

            # _check_order_info > _has_open_interest > {'api': 'get_account_openposition', 'success': True,
            # 'result': '[{"product": "MXFI0", "action": "Buy", "qty": 1, "price": 12608, "real_price": 12530}]'}

            if not response['success']:
                return response

            positions = json.loads(response['result'])
            for position in positions:
                if position['product'] == product and position['action'] == expected:
                    return dict(
                        api='check_order_info',
                        success=True,
                        result=json.dumps(position)
                    )
            if time.time() - stime > timeout:
                return dict(
                    api='get_account_openposition',
                    success=False,
                    result='no expected position found'
                )
            retry += 1
            time.sleep(retry)
            print('_check_order_info start retry %s' % retry)

    def _wrap_place_order_result(self, result):
        wrap_result = dict(
            product=result.contract.code,
            order=str(result.order.action),
            price=str(result.order.price),
            qty=result.order.quantity,
            price_type=str(result.order.price_type),
            order_type=str(result.order.order_type),
            status=str(result.status.status),
            order_time=str(result.status.order_datetime)
        )
        return json.dumps(wrap_result)

    def _place_order(self, product, order_type, price=0, qty=1, trade_type=ORDER_REST_OF_DAY):
        try:
            contract = self._retry_get_contract(product)
            print('_place_order > contract for %s > %s' % (product, contract))

            order = self._retry_create_order(order_type, price, qty, trade_type)

            result = self._retry_place_order(contract, order)
            order_status = result.status
            print('_place_order > order_status > %s' % order_status)

            success = False if order_status.status == Status.Failed else True
            return dict(
                api='place_order',
                success=success,
                result=self._wrap_place_order_result(result)
            )

        except Exception as e:
            print('_place_order > Error: %s' % traceback.format_exc())
            return dict(
                api='place_order',
                success=False,
                result=str(e)
            )

    def _retry_place_order(self, contract, order):
        retry = 0
        result = None
        while True:
            try:
                result = self.api.place_order(contract, order)

            except:
                print('_retry_place_order > Error on place order %s' % traceback.format_exc())

            if result and result.status not in [Status.Inactive, Status.Failed, Status.Cancelled]:
                return result

            if retry > 3:
                raise Exception('_retry_place_order > Failed to place order for %s %s' % (contract, order))

            print('Got failed status in place_order %s, do login and retry' % result)
            if not self.account:
                self._do_login()
            time.sleep(retry)
            retry += 1
            print('_retry_place_order start retry %s' % retry)

    def _retry_create_order(self, order_type, price, qty, trade_type):
        retry = 0
        order = None
        while True:
            try:
                order = self.api.Order(action="Buy" if order_type == ORDER_TYPE_BUY else "Sell",
                                       price=price,
                                       quantity=qty,
                                       order_type=trade_type,
                                       price_type=ORDER_PRICE_MARKET if price == 0 else ORDER_PRICE_LIMIT,
                                       octype="Auto",
                                       account=self.account)
            except:
                print('_retry_create_order > Error on create Order %s' % traceback.format_exc())
            if order:
                return order
            if retry > 3:
                raise Exception('_retry_create_order > Failed to create order for %s %s' % (order_type, price))
            time.sleep(retry)
            retry += 1
            print('_retry_create_order start retry %s ' % retry)

    def _retry_get_contract(self, product):
        retry = 0
        contract = None
        while True:
            try:
                contract = self.api.Contracts.Futures[product]
            except:
                print('_retry_get_contract > Error on get Contract %s' % traceback.format_exc())
            if contract:
                return contract
            if retry > 5:
                raise Exception('_retry_get_contract > Failed to get contract for %s' % product)
            if not self.account:
                self._do_login()
            time.sleep(retry)
            retry += 1
            print('_retry_get_contract start retry %s' % retry)

    def _mayday(self, product):
        print('_mayday > product: %s' % product)
        responses = []
        try:
            # response = self._do_login()
            # if not response['success']:
            #     return response

            response = self._has_open_interest()
            print('_mayday > _has_open_interest > %s' % response)
            if not response['success']:
                return response

            positions = json.loads(response['result'])
            if not positions:
                responses.append(dict(
                    api='mayday',
                    success=True,
                    result='no open positions'
                ))
                return responses

            for position in positions:
                if position['product'] == product:
                    responses.append(self._place_order(
                        product=product,
                        order_type=ORDER_TYPE_BUY if position['action'] == Action.Sell else ORDER_TYPE_SELL,
                        trade_type=ORDER_IMMEDIATE_OR_CANCEL,
                        price=0))
                    print('_mayday > _place_order > %s' % responses[-1])
                    if not responses[-1]['success']:
                        return responses
            return responses

        except Exception as e:
            logger.error(traceback.format_exc())
            response = dict(
                api='mayday',
                success=False,
                result=str(e)
            )
            responses.append(response)
            return responses

    def HasOpenInterest(self, product):
        print('HasOpenInterest > product: %s' % product)
        responses = []
        responses.append(self._has_open_interest())
        return responses

    def CloseAndBuy(self, product, price):
        print('CloseAndBuy > product: %s, price: %s' % (product, price))
        responses = []
        # responses.append(self._do_login())
        # if not responses[-1]['success']:
        #     return responses

        responses.append(self._has_open_interest())
        print('CloseAndBuy > _has_open_interest > %s' % responses[-1])
        if not responses[-1]['success']:
            return responses

        # close first, verify the open interest is SELL
        open_positions = json.loads(responses[-1]['result'])
        for position in open_positions:
            if position['product'] == product and position['action'] == Action.Sell:
                responses.append(self._place_order(product, ORDER_TYPE_BUY, price))
                print('CloseAndBuy > _place_order for close > %s' % responses[-1])
                if not responses[-1]['success']:
                    return responses

            elif position['action'] == Action.Buy:
                return responses

        # then buy
        responses.append(self._place_order(product, ORDER_TYPE_BUY, price))
        print('CloseAndBuy > _place_order for buy > %s' % responses[-1])
        if not responses[-1]['success']:
            return responses

        # check buy posisition
        responses.append(self._check_order_info(product, Action.Buy))
        print('CloseAndBuy > _check_order_info > %s' % responses[-1])
        return responses

    def CloseAndSell(self, product, price):
        print('CloseAndSell > product: %s, price: %s' % (product, price))
        responses = []
        # responses.append(self._do_login())
        # if not responses[-1]['success']:
        #     return responses

        responses.append(self._has_open_interest())
        print('CloseAndSell > _has_open_interest > %s' % responses[-1])
        if not responses[-1]['success']:
            return responses

        # close first, verify the open interest is Buy
        open_positions = json.loads(responses[-1]['result'])
        for position in open_positions:
            if position['product'] == product and position['action'] == Action.Buy:
                responses.append(self._place_order(product, ORDER_TYPE_SELL, price))
                print('CloseAndSell > _place_order for close > %s' % responses[-1])
                if not responses[-1]['success']:
                    return responses

            elif position['action'] == Action.Sell:
                return responses

        # then sell
        responses.append(self._place_order(product, ORDER_TYPE_SELL, price))
        if not responses[-1]['success']:
            print('CloseAndSell > _place_order for sell > %s' % responses[-1])
            return responses

        # check sell posisition
        responses.append(self._check_order_info(product, Action.Sell))
        print('CloseAndSell > _check_order_info > %s' % responses[-1])
        return responses

    def MayDay(self, product):
        print('MayDay > product: %s' % product)
        return self._mayday(product)
