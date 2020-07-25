import time, json
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

        api = sj.Shioaji(backend='http', simulation=False)
        api.login(
            self.config.get('shioaj_api', 'person_id'),
            self.config.get('shioaj_api', 'passwd')
        )
        logger.info(api.list_accounts())

        self.account = [a for a in api.list_accounts() if a.account_id == self.config.get('shioaj_api', 'account_id')][
            0]
        logger.info('Set default account: %s' % self.account)

        api.set_default_account(self.account)
        logger.info('CA path: %s' % self.config.get('shioaj_api', 'ca_path'))
        api.activate_ca(
            ca_path=self.config.get('shioaj_api', 'ca_path'),
            ca_passwd=self.config.get('shioaj_api', 'ca_passwd'),
            person_id=self.config.get('shioaj_api', 'person_id')
        )
        self.api = api

    def _wrap_list_positions_result(self, results):
        # code (str): contract id.
        # direction (Action): action.
        #     {Buy, Sell}
        # quantity (int): quantity.
        # price (float): the average price.
        # pnl (float): unrealized profit.
        # yd_quantity (int): yesterday
        # cond (StockOrderCond): Default Cash.
        #     {Cash, Netting, MarginTrading, ShortSelling}

        wrap_results = [dict(
            product=result.code,
            direction=str(result.direction),
            qty=result.quantity,
            price=str(result.price),
            unrealized_profit=str(result.pln)
        ) for result in results]
        return json.dumps(wrap_results)

    def _has_open_interest(self):
        retry = 0
        while True:
            try:
                result = self.api.list_positions(self.account)
                return dict(
                    api='list_positions',
                    success=True,
                    result=self._wrap_list_positions_result(result)
                )

            except Exception as e:
                retry += 1
                if retry > 3:
                    print(traceback.format_exc())
                    return dict(
                        api='list_positions',
                        success=False,
                        result=str(e)
                    )
                time.sleep(retry)

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
            contract = self.api.Contracts.Futures[product]
            print(contract)

            order = self.api.Order(action="Buy" if order_type == ORDER_TYPE_BUY else "Sell",
                                   price=price,
                                   quantity=qty,
                                   order_type=trade_type,
                                   price_type=ORDER_PRICE_MARKET if price == 0 else ORDER_PRICE_LIMIT,
                                   octype="Auto",
                                   account=self.account)

            result = self.api.place_order(contract, order, timeout=10000)
            order_status = result.status
            success = False if order_status.status == Status.Failed else True
            return dict(
                api='place_order',
                success=success,
                result=self._wrap_place_order_result(result)
            )

        except Exception as e:
            logger.info(traceback.format_exc())
            return dict(
                api='place_order',
                success=False,
                result=str(e)
            )

    def _mayday(self, product):
        try:
            responses = []
            positions = self.api.list_positions(self.account)
            if not positions:
                responses.append(dict(
                    api='mayday',
                    success=True,
                    result='no open positions'
                ))
                return responses

            for position in positions:
                responses.append(self._place_order(
                    product=position.code,
                    order_type=ORDER_TYPE_BUY if position.direction == Action.Sell else ORDER_TYPE_SELL,
                    price=0))
                if not responses[-1]['success']:
                    return responses
            return responses

        except Exception as e:
            logger.info(traceback.format_exc())
            return dict(
                api='mayday',
                success=False,
                result=str(e)
            )

    def HasOpenInterest(self, product):
        responses = []
        responses.append(self._has_open_interest())
        return responses

    def CloseAndBuy(self, product, price):
        responses = []

        responses.append(self._has_open_interest())
        if not responses[-1]['success']:
            return responses

        # close first, verify the open interest is SELL
        open_positions = json.loads(responses[-1]['result'])
        for position in open_positions:
            if position.direction == Action.Sell:
                responses.append(self._place_order(product, ORDER_TYPE_BUY, price))
                if not responses[-1]['success']:
                    return responses

            elif position.direction == Action.Buy:
                return responses

        # then buy
        responses.append(self._place_order(product, ORDER_TYPE_BUY, price))
        return responses

    def CloseAndSell(self, product, price):
        responses = []

        responses.append(self._has_open_interest())
        if not responses[-1]['success']:
            return responses

        # close first, verify the open interest is Buy
        open_positions = json.loads(responses[-1]['result'])
        for position in open_positions:
            if position.direction == Action.Buy:
                responses.append(self._place_order(product, ORDER_TYPE_SELL, price))
                if not responses[-1]['success']:
                    return responses

            elif position.direction == Action.Sell:
                return responses

        # then buy
        responses.append(self._place_order(product, ORDER_TYPE_SELL, price))
        return responses

    def MayDay(self, product):
        return self._mayday(product)
