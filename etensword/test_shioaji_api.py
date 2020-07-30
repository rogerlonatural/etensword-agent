from etensword.api.base import OrderAgentFactory
import shioaji as sj
import pandas as pd

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

def test():
    api = sj.Shioaji(simulation=True)
    api.login(
        person_id="PAPIUSER01",
        passwd="2222"
    )


    print(api.list_accounts())
    account = api.list_accounts()[0]

    contract = api.Contracts.Futures.TXF.TXF202008
    print(contract)

    order = api.Order(
        action="Buy",
        price=9000,
        quantity=1,
        order_type="ROD",
        price_type="LMT",
        octype="Auto",
        account=account
    )
    print(order)

    trade = api.place_order(contract, order)
    print(trade)



    positions = api.get_account_openposition(query_type='1', account=account)
    df_positions = pd.DataFrame(positions.data())
    print(df_positions)


def main():
    # test_shioaji_api_close_and_buy()
    # test_shioaji_api_has_open_interest()
    test()



if __name__ == '__main__':
    main()