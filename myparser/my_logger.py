import logging.handlers
import logging
import pathlib

from myparser.config import config

logging_level = config['level'].upper()

def get_logger(name):

    logging.basicConfig(level=logging_level, filemode='a')
    logging.getLogger('pdfminer').setLevel('WARNING') 
    logging.getLogger('matplotlib').setLevel('WARNING') 
    logging.getLogger('camelot').setLevel('WARNING') 
    

    cwd = pathlib.Path(__file__).parent.resolve()
    file = cwd/'parsing.log'

    log_format = logging.Formatter(
        '%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s')

    f_handler = logging.FileHandler(filename=str(file), mode='a')
    f_handler.setLevel(logging_level)
    f_handler.setFormatter(log_format)

    logger = logging.getLogger(name)
    logger.addHandler(f_handler)

    return logger
