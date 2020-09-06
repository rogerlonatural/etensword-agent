import pandas as pd
import shioaji as sj

from etensword import get_config
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
    # test()

    config = get_config()
    agent_id_options = config.options('agent_account_mapping')
    agent_account_mapping = { agent_id: config.get('agent_account_mapping', agent_id) for agent_id in agent_id_options}
    print(agent_account_mapping)


if __name__ == '__main__':
    main()