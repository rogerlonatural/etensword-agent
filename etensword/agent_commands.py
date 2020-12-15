class AgentCommand(object):
    COMMAND_TIMEOUT = 300  # seconds

    ENABLE_AGENT = 'ENABLE_AGENT'
    DISABLE_AGENT = 'DISABLE_AGENT'
    CHECK_AGENT = 'Hi, how are you?'
    MAYDAY = 'MAYDAY'
    CHECK_OPEN_INTEREST = 'CHECK_OPEN_INTEREST'
    CLOSE_OPEN_INTEREST = 'CLOSE_OPEN_INTEREST'
    CLOSE_AND_BUY = 'CLOSE_AND_BUY'
    CLOSE_AND_SELL = 'CLOSE_AND_SELL'
    BUY = 'BUY'
    SELL = 'SELL'