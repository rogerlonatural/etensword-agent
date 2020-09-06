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
    __instance = None
    __last_login_time = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if OrderAgent.__instance == None:
            OrderAgent()
        return OrderAgent.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if OrderAgent.__instance != None:
            raise Exception("This class is a singleton, use getInstance() instead!")

        super().__init__()

        self.api = sj.Shioaji(backend='http', simulation=False)
        self.person_id = self.config.get('shioaj_api', 'person_id')
        self.passwd = self.config.get('shioaj_api', 'passwd')
        self.ca_passwd = self.config.get('shioaj_api', 'ca_passwd')
        self.ca_path = self.config.get('shioaj_api', 'ca_path')

        agent_ids = self.config.options('agent_account_mapping')
        self.agent_account_mapping = {agent_id: self.config.get('agent_account_mapping', agent_id) for agent_id in
                                      agent_ids}
        self.account = None
        logger.info('<== Agent created with build version')  # use logger to print build version

        self._do_login()

        OrderAgent.__last_login_time = time.time()
        OrderAgent.__instance = self


    def __del__(self):
        self._do_logout()

    def _do_logout(self):
        try:
            print('[%s] Logout and leave' % self.trace_id)
            if self.api:
                self.api.logout()
        except:
            print('[%s] Error on __del__, ignored %s' % (self.trace_id, traceback.format_exc().replace('\n', ' >> ')))

    def _set_account(self, agent_id):
        self.account_id = self.agent_account_mapping[agent_id]
        print('[%s] Set account %s' % (self.trace_id, self.account_id))

        all_accounts = self.api.list_accounts()
        print('[%s] Login successfully and list accounts >>> %s' % (self.trace_id, all_accounts))
        for fa in all_accounts:
            if fa.account_id == self.account_id:
                self.account = fa
                print('[%s] Login with account_id: %s' % (self.trace_id, self.account.account_id))
                break

        if not self.account:
            raise Exception('No account for account_id: %s' % self.account_id)

        print('[%s] Set default account: %s' % (self.trace_id, self.account))
        self.api.set_default_account(self.account)

    def _do_login(self):
        retry = 0
        while True:
            try:
                self.api.login(self.person_id, self.passwd)

                print('[%s] Initialize CA: %s' % (self.trace_id, self.ca_path))
                self.api.activate_ca(
                    ca_path=self.ca_path,
                    ca_passwd=self.ca_passwd,
                    person_id=self.person_id
                )

                return dict(
                    api='login',
                    success=True,
                    result='Login with person_id: %s' % self.person_id
                )

            except Exception as e:
                if self.person_id and self.passwd:
                    print('[%s] Failed to login with id: %s****, pwd: %s**** . Error: %s' % (
                        self.trace_id, self.person_id[0], self.passwd[0], traceback.format_exc().replace('\n', '>>')))

                if retry > 3:
                    print('[%s] Login failed after retry. %s' % (
                        self.trace_id, traceback.format_exc().replace('\n', ' >> ')))
                    return dict(
                        api='login',
                        success=False,
                        result=str(e)
                    )

            retry += 1
            time.sleep(retry)
            print('[%s] _do_login start retry %s' % (self.trace_id, retry))

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
                    return dict(
                        api='get_account_openposition',
                        success=False,
                        result='Not login yet, account: %s' % self.account
                    )

                positions = self.api.get_account_openposition(product_type="0", query_type="0", account=self.account)
                print(
                    '[%s] _has_open_interest > get_account_openposition > data: %s' % (self.trace_id, positions.data()))

                return dict(
                    api='get_account_openposition',
                    success=True,
                    result=self._wrap_get_account_openposition_data(positions.data())
                )
            except Exception as e:
                if retry > 3:
                    print('[%s] _has_open_interest with account %s. Error: %s' % (
                        self.trace_id, self.account, traceback.format_exc().replace('\n', ' >> ')))
                    return dict(
                        api='get_account_openposition',
                        success=False,
                        result=str(e)
                    )
            time.sleep(retry)
            retry += 1
            print('[%s] _has_open_interest start retry %s' % (self.trace_id, retry))

    def _check_order_info(self, product, expected, timeout=60):
        print('[%s] _check_order_info > product: %s, expected: %s' % (self.trace_id, product, expected))
        stime = time.time()
        retry = 0
        while True:
            response = self._has_open_interest()
            print('[%s] _check_order_info > _has_open_interest > %s' % (self.trace_id, response))

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
            print('[%s] _check_order_info start retry %s' % (self.trace_id, retry))

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
            print('[%s] _place_order > contract for %s > %s' % (self.trace_id, product, contract))

            order = self._retry_create_order(order_type, price, qty, trade_type)

            result = self._retry_place_order(contract, order)
            order_status = result.status
            print('[%s] _place_order > order_status > %s' % (self.trace_id, order_status))

            success = False if order_status.status == Status.Failed else True
            return dict(
                api='place_order',
                success=success,
                result=self._wrap_place_order_result(result)
            )

        except Exception as e:
            print('[%s] _place_order > Error: %s' % (self.trace_id, traceback.format_exc().replace('\n', ' >> ')))
            return dict(
                api='place_order',
                success=False,
                result=str(e)
            )

    def _retry_place_order(self, contract, order):
        retry = 0
        while True:
            try:
                result = self.api.place_order(contract, order, timeout=30000)
                print('[%s] place order result %s' % (self.trace_id, result))

                if not result:
                    raise Exception('Failed to place order: %s' % result)

                if result.status in [Status.Inactive, Status.Failed, Status.Cancelled, 'Inactive']:
                    raise Exception('Got failed status in place_order %s, retry' % result.status)

                return result

            except:
                print('[%s] _retry_place_order > Error on place order %s' % (
                    self.trace_id, traceback.format_exc().replace('\n', ' >> ')))

            if retry > 3:
                raise Exception('_retry_place_order > Failed to place order for %s %s' % (contract, order))

            time.sleep(retry)
            retry += 1
            print('[%s] _retry_place_order start retry %s' % (self.trace_id, retry))

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
                print('[%s] _retry_create_order > Error on create Order %s' % (
                    self.trace_id, traceback.format_exc().replace('\n', ' >> ')))
            if order:
                return order
            if retry > 3:
                raise Exception('_retry_create_order > Failed to create order for %s %s' % (order_type, price))
            time.sleep(retry)
            retry += 1
            print('[%s] _retry_create_order start retry %s ' % (self.trace_id, retry))

    def _retry_get_contract(self, product):
        retry = 0
        contract = None
        while True:
            try:
                contract = self.api.Contracts.Futures[product]
            except:
                print('[%s] _retry_get_contract > Error on get Contract %s' % (
                    self.trace_id, traceback.format_exc().replace('\n', ' >> ')))
            if contract:
                return contract
            if retry > 5:
                raise Exception('_retry_get_contract > Failed to get contract for %s' % product)

            time.sleep(retry)
            retry += 1
            print('[%s] _retry_get_contract start retry %s' % (self.trace_id, retry))

    def _mayday(self, product):
        print('[%s] _mayday > product: %s' % (self.trace_id, product))
        responses = []
        try:
            # response = self._do_login()
            # if not response['success']:
            #     return response

            response = self._has_open_interest()
            print('[%s] _mayday > _has_open_interest > %s' % (self.trace_id, response))
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
                    print('[%s] _mayday > _place_order > %s' % (self.trace_id, responses[-1]))
                    if not responses[-1]['success']:
                        return responses
            return responses

        except Exception as e:
            logger.error(traceback.format_exc().replace('\n', ' >> '))
            response = dict(
                api='mayday',
                success=False,
                result=str(e)
            )
            responses.append(response)
            return responses

    def InitAgent(self, agent_id):

        if time.time() - OrderAgent.__last_login_time > 60 * 60 * 3:
            self._do_logout()
            self._do_login()
            OrderAgent.__last_login_time = time.time()

        self._set_account(agent_id)

    def HasOpenInterest(self, product):
        print('[%s] HasOpenInterest > product: %s' % (self.trace_id, product))
        responses = []
        responses.append(self._has_open_interest())
        return responses

    def CloseAndBuy(self, product, price):
        print('[%s] CloseAndBuy > product: %s, price: %s' % (self.trace_id, product, price))
        responses = []
        # responses.append(self._do_login())
        # if not responses[-1]['success']:
        #     return responses

        responses.append(self._has_open_interest())
        print('[%s] CloseAndBuy > _has_open_interest > %s' % (self.trace_id, responses[-1]))
        if not responses[-1]['success']:
            return responses

        # close first, verify the open interest is SELL
        open_positions = json.loads(responses[-1]['result'])
        for position in open_positions:
            if position['product'] == product and position['action'] == Action.Sell:
                responses.append(self._place_order(product, ORDER_TYPE_BUY, price))
                print('[%s] CloseAndBuy > _place_order for close > %s' % (self.trace_id, responses[-1]))
                if not responses[-1]['success']:
                    return responses

            elif position['action'] == Action.Buy:
                return responses

        # then buy
        responses.append(self._place_order(product, ORDER_TYPE_BUY, price))
        print('[%s] CloseAndBuy > _place_order for buy > %s' % (self.trace_id, responses[-1]))
        if not responses[-1]['success']:
            return responses

        # check buy posisition
        responses.append(self._check_order_info(product, Action.Buy))
        print('[%s] CloseAndBuy > _check_order_info > %s' % (self.trace_id, responses[-1]))
        return responses

    def CloseAndSell(self, product, price):
        print('[%s] CloseAndSell > product: %s, price: %s' % (self.trace_id, product, price))
        responses = []
        # responses.append(self._do_login())
        # if not responses[-1]['success']:
        #     return responses

        responses.append(self._has_open_interest())
        print('[%s] CloseAndSell > _has_open_interest > %s' % (self.trace_id, responses[-1]))
        if not responses[-1]['success']:
            return responses

        # close first, verify the open interest is Buy
        open_positions = json.loads(responses[-1]['result'])
        for position in open_positions:
            if position['product'] == product and position['action'] == Action.Buy:
                responses.append(self._place_order(product, ORDER_TYPE_SELL, price))
                print('[%s] CloseAndSell > _place_order for close > %s' % (self.trace_id, responses[-1]))
                if not responses[-1]['success']:
                    return responses

            elif position['action'] == Action.Sell:
                return responses

        # then sell
        responses.append(self._place_order(product, ORDER_TYPE_SELL, price))
        if not responses[-1]['success']:
            print('[%s] CloseAndSell > _place_order for sell > %s' % (self.trace_id, responses[-1]))
            return responses

        # check sell posisition
        responses.append(self._check_order_info(product, Action.Sell))
        print('[%s] CloseAndSell > _check_order_info > %s' % (self.trace_id, responses[-1]))
        return responses

    def MayDay(self, product):
        print('[%s] MayDay > product: %s' % (self.trace_id, product))
        return self._mayday(product)
