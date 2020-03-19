import logging


def setup_logger(name, log_file, level=None, mode='w', clean_up=False):
    if clean_up:
        logging.Logger.manager.loggerDict.clear()

    if not level:
        level = logging.INFO
    formatter = logging.Formatter('%(name)s %(levelname)s %(message)s')

    handler = logging.FileHandler(log_file, mode=mode)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
