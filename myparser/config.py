import logging.handlers
import logging
import pathlib


def get_logger(name):

    logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s',
                        level=logging.DEBUG, filemode='a')

    cwd = pathlib.Path(__file__).parent.resolve()
    file = cwd/'parsing.log'

    f_handler = logging.FileHandler(filename=str(file), mode='a')
    f_format = logging.Formatter(
        '%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s')
    f_handler.setFormatter(f_format)

    logger = logging.getLogger(name)
    logger.addHandler(f_handler)

    return logger
