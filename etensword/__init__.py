import os
from configparser import ConfigParser


def get_config(argv=None):
    ini_file = os.getenv('ETENSWORD_AGENT_CONF')
    if not ini_file:
        if argv and len(argv) > 0:
            ini_file = argv[0]
    if not ini_file:
        print('No ini file path provided, use settings.ini by default.')
        ini_file = "settings.ini"
    config = ConfigParser()
    config.read(ini_file)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.get('gcp', 'GOOGLE_APPLICATION_CREDENTIALS')
    return config