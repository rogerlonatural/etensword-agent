from unittest import TestCase

from etensword.api.base import OrderAgentFactory


class TestOrderAgent(TestCase):
    def test_close_and_sell(self):
        agent = OrderAgentFactory.get_order_agent('smart_api')
        result = agent.CloseAndSell('MXFF0', 10000)
        print(result)

    def test_close_and_buy(self):
        agent = OrderAgentFactory.get_order_agent('smart_api')
        result = agent.CloseAndBuy('MXFF0', 10000)
        print(result)


    def test__get_account(self):
        agent = OrderAgentFactory.get_order_agent('smart_api')
        result = agent._get_account('ordernumber1', 0)
        print(result)
        result = agent._get_account('ordernumber1', 1)
        print(result)




