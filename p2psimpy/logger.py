import logging.config
import yaml


def init_log():
    with open('/Users/bulat/projects/tudelft/BlockchainEngineering/p2psimpy/input/logger.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)