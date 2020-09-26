from unittest import TestCase

from etensword.api.base import OrderAgentFactory


class TestOrderAgent(TestCase):
    def test_smart_api_close_and_sell(self):
        agent = OrderAgentFactory.get_order_agent('smart_api')
        result = agent.CloseAndSell('MXFF0', 10000)
        print(result)

    def test_smart_api_close_and_buy(self):
        agent = OrderAgentFactory.get_order_agent('smart_api')
        result = agent.CloseAndBuy('MXFF0', 10000)
        print(result)


    def test_smart_api_get_account(self):
        agent = OrderAgentFactory.get_order_agent('smart_api')
        result = agent._get_account('ordernumber1')
        print(result)
        result = agent._get_account('ordernumber1')
        print(result)

    def test_shioaji_api_close_and_sell(self):
        agent = OrderAgentFactory.get_order_agent('shioaji_api')
        result = agent.CloseAndSell('MXFF0', 10000)
        print(result)

    def test_shioaji_api_close_and_buy(self):
        agent = OrderAgentFactory.get_order_agent('shioaji_api')
        result = agent.CloseAndBuy('MXFF0', 10000)
        print(result)


    def test_shioaji_api_has_open_interest(self):
        agent = OrderAgentFactory.get_order_agent('shioaji_api')
        result = agent.HasOpenInterest('MXFF0')
        print(result)

    def test_shioaji_api_mayday(self):
        agent = OrderAgentFactory.get_order_agent('shioaji_api')
        result = agent.MayDay('MXFF0')
        print(result)


