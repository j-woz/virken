
# LOG TOOLS

# Standardize some Python logging techniques

import logging

logger_handler = None

def logger_init(enabled=True):
    """ Set up the log file pointer.    """
    """ Run this before starting curses """
    global logger_fp, logger_handler
    import os
    log_dir  = os.getenv("VCMENU_TMP")
    log_file = log_dir + "/vcmenu.log"
    try:
        logger_fp = open(log_file, "a")
        logger_handler = logging.StreamHandler(stream=logger_fp)
        fmtr = logging.Formatter('%(asctime)s %(name)-10s ' +
                                 '%(levelname)-7s ' +
                                 '%(message)s',
                                 datefmt='%H:%M:%S')
        logger_handler.setFormatter(fmtr)
    except Exception as e:
        print("Could not open log file: " + log_file + "\n" +
              str(e))
        return False
    return True

def logger_get(logger, name):
    """ Set up logging """
    if logger is not None:
        return logger
    import logging
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    global logger_fp, logger_handler
    # print("logger handler: " + str(logger_handler))
    logger.addHandler(logger_handler)
    return logger
