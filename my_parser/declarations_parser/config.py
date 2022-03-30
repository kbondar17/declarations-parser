import logging.handlers
import logging
import pathlib


def get_logger(name):

    logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s %(message)s',
                        level=logging.DEBUG, filemode='a')

    cwd = pathlib.Path(__file__).parent.resolve()

    f_handler = logging.FileHandler(filename=cwd/'parsing.log')
    logger = logging.getLogger(name)
    print(cwd/'file.log')
    logger.addHandler(f_handler)
    return logger
