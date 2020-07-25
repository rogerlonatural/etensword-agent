from etensword.api.base import OrderAgentFactory


def test_shioaji_api_close_and_buy():
    agent = OrderAgentFactory.get_order_agent('shioaji_api')
    result = agent.CloseAndBuy('MXFH0', 10000)
    print(result)


def test_shioaji_api_has_open_interest():
    agent = OrderAgentFactory.get_order_agent('shioaji_api')
    result = agent.HasOpenInterest('MXFH0')
    print(result)


def test_shioaji_api_mayday():
    agent = OrderAgentFactory.get_order_agent('shioaji_api')
    result = agent.MayDay('MXFH0')
    print(result)


def main():
    # test_shioaji_api_close_and_buy()
    test_shioaji_api_has_open_interest()


if __name__ == '__main__':
    main()