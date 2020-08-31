from configparser import ConfigParser

def read_config():
    file = 'config.ini'
    config = ConfigParser()
    config.read(file)
    configuration = config['EMAIL_CRED']
    return configuration

#read_config_function = read_config()

#print(read_config_function['EMAIL_SUBJECT'])