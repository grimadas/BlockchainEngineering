import logging.config
import yaml


def init_log():
    with open('/Users/bulat/projects/tudelft/BlockchainEngineering/p2psimpy/input/logger.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)


def reset_log():
    with open('/Users/bulat/projects/tudelft/BlockchainEngineering/p2psimpy/input/logger.yml', 'r') as f:
        config = yaml.safe_load(f.read())
        log_filename = config['handlers']['file']['filename']
        import os
        try:
            os.remove(log_filename)
        except OSError:
            pass
