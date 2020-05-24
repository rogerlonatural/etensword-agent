from unittest import TestCase

from etensword.order_agent import OrderAgent


class TestOrderAgent(TestCase):
    def test_close_and_sell(self):
        agent = OrderAgent()
        agent.CloseAndSell('MXFF0', 10000)

    def test_close_and_buy(self):
        agent = OrderAgent()
        agent.CloseAndBuy('MXFF0', 10000)


    def test__get_account(self):
        agent = OrderAgent()
        result = agent._get_account('ordernumber1', 0)
        print(result)
        result = agent._get_account('ordernumber1', 1)
        print(result)




