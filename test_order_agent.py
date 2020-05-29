from unittest import TestCase

from etensword.api import OrderAgent


class TestOrderAgent(TestCase):
    def test_close_and_sell(self):
        agent = OrderAgent()
        result = agent.CloseAndSell('MXFF0', 10000)
        print(result)

    def test_close_and_buy(self):
        agent = OrderAgent()
        result = agent.CloseAndBuy('MXFF0', 10000)
        print(result)


    def test__get_account(self):
        agent = OrderAgent()
        result = agent._get_account('ordernumber1', 0)
        print(result)
        result = agent._get_account('ordernumber1', 1)
        print(result)




